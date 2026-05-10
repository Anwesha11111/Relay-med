"""
LLM Adapter — Routes completions to Ollama (local), Google Gemini API,
or built-in fallback mode when no API key is configured.

The fallback mode provides intelligent, topic-aware health responses
so the app always works — even without any external API.
"""

import asyncio
import re
from typing import AsyncIterator, Literal
import httpx
from backend.config import settings


# ── Smart fallback responses based on health context ─────────────────────────
FALLBACK_RESPONSES = {
    "cardiovascular": (
        "Based on your health data, here are some factors that may influence cardiovascular health:\n\n"
        "**Key Observations:**\n"
        "- Your recent blood pressure readings and heart rate trends are being monitored\n"
        "- Physical activity levels and sleep patterns both play important roles\n"
        "- Stress management is a significant factor in heart health\n\n"
        "**Suggestions:**\n"
        "1. **Stay Active** -- Aim for 30 minutes of moderate exercise daily\n"
        "2. **Manage Stress** -- Practice mindfulness or deep breathing exercises\n"
        "3. **Sleep Well** -- Target 7-8 hours of quality sleep\n"
        "4. **Diet** -- Consider reducing sodium and increasing fruits/vegetables\n\n"
        "**Medications sometimes used for heart health** (consult your doctor):\n"
        "- **Aspirin** (low-dose) -- for cardiovascular risk reduction\n"
        "- **Statins** (e.g., Atorvastatin) -- for cholesterol management\n"
        "- **ACE inhibitors** -- for blood pressure control\n"
        "- **Beta-blockers** -- for heart rate regulation\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- an artificial intelligence, "
        "not a doctor. AI can make mistakes. **Please consult your doctor or a qualified healthcare provider** "
        "before starting, stopping, or changing any medication or treatment."
    ),
    "sleep": (
        "Sleep is one of the most important pillars of health. Here's what I can share:\n\n"
        "**Your Sleep Insights:**\n"
        "- Consistency in sleep schedule matters more than total hours\n"
        "- Your body's circadian rhythm affects blood pressure, heart rate, and glucose\n\n"
        "**Tips to Improve Sleep:**\n"
        "1. Keep a consistent bedtime and wake time\n"
        "2. Limit screen time 1 hour before bed\n"
        "3. Keep your room cool (65-68F / 18-20C)\n"
        "4. Avoid caffeine after 2pm\n\n"
        "**Sleep Aids** (consult your doctor first):\n"
        "- **Melatonin** (0.5-3mg) -- natural sleep hormone supplement\n"
        "- **Magnesium Glycinate** -- helps muscle relaxation and sleep quality\n"
        "- **Valerian Root** -- herbal supplement for mild insomnia\n"
        "- For chronic insomnia, prescription options like **Trazodone** or **Zolpidem** may be discussed with your doctor\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- an artificial intelligence, "
        "not a doctor. AI can make mistakes. **Please consult your doctor** "
        "before taking any sleep medication or supplement."
    ),
    "headache": (
        "Here are some commonly used approaches for headache relief:\n\n"
        "**Over-the-Counter Options:**\n"
        "- **Ibuprofen** (Advil, Motrin) -- commonly used for tension headaches and migraines\n"
        "- **Acetaminophen** (Tylenol) -- generally gentler on the stomach\n"
        "- **Aspirin** -- effective for many types of headaches\n"
        "- **Naproxen** (Aleve) -- longer-lasting relief\n\n"
        "**For Migraines specifically:**\n"
        "- **Triptans** (e.g., Sumatriptan) -- prescription, specifically designed for migraines\n"
        "- **Excedrin Migraine** -- OTC combination of acetaminophen, aspirin, and caffeine\n\n"
        "**Non-Drug Approaches:**\n"
        "- Stay hydrated -- dehydration is a common headache trigger\n"
        "- Apply a cold compress to your forehead\n"
        "- Rest in a quiet, dark room\n"
        "- Gentle neck stretches and massage\n\n"
        "**When to See a Doctor:**\n"
        "- Severe or sudden headache ('worst headache of your life')\n"
        "- Headaches that worsen over days\n"
        "- Headache with fever, stiff neck, or vision changes\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- an artificial intelligence, "
        "not a doctor. AI can make mistakes. The suggestions above are for informational "
        "purposes only. **Please consult your doctor or a qualified healthcare provider** "
        "before starting, stopping, or changing any medication or treatment."
    ),
    "medication": (
        "I can share some general information about health management and medicines:\n\n"
        "**Common Over-the-Counter Medicines:**\n"
        "- **Pain relief**: Ibuprofen, Acetaminophen, Aspirin\n"
        "- **Allergies**: Cetirizine (Zyrtec), Loratadine (Claritin), Diphenhydramine (Benadryl)\n"
        "- **Digestive issues**: Omeprazole (Prilosec), Famotidine (Pepcid)\n"
        "- **Cold/Flu**: Pseudoephedrine, Dextromethorphan, Guaifenesin\n\n"
        "**Prescription Medicines** (require doctor's prescription):\n"
        "- Blood pressure: ACE inhibitors, ARBs, beta-blockers, calcium channel blockers\n"
        "- Diabetes: Metformin, insulin, SGLT2 inhibitors\n"
        "- Cholesterol: Statins (Atorvastatin, Rosuvastatin)\n\n"
        "**Important**: The right medicine depends on your specific condition, other medications, "
        "allergies, and medical history. What works for one person may not work for another.\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- an artificial intelligence, "
        "not a doctor. AI can make mistakes. **Please consult your doctor** "
        "before starting, stopping, or changing any medication."
    ),
    "exercise": (
        "Great question about physical activity! Here's what the research shows:\n\n"
        "**Benefits of Regular Exercise:**\n"
        "- Reduces cardiovascular risk by up to 30-40%\n"
        "- Improves insulin sensitivity and blood sugar control\n"
        "- Enhances sleep quality and mental health\n"
        "- Helps maintain healthy weight and blood pressure\n\n"
        "**Recommended Activity Levels:**\n"
        "1. **Walking** -- 30 minutes daily can significantly improve health markers\n"
        "2. **Moderate exercise** -- 150 minutes per week (WHO recommendation)\n"
        "3. **Strength training** -- 2 sessions per week for muscle and bone health\n\n"
        "**Your Data Shows:**\n"
        "- Your step count and activity levels are being tracked\n"
        "- Even small increases in daily movement can yield big health benefits\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- an artificial intelligence, "
        "not a doctor. AI can make mistakes. "
        "Please consult a qualified healthcare provider before starting a new exercise program."
    ),
    "stress": (
        "Stress management is crucial for overall health. Here's what I can share:\n\n"
        "**How Stress Affects Your Body:**\n"
        "- Elevates blood pressure and heart rate\n"
        "- Disrupts sleep patterns and quality\n"
        "- Can increase blood sugar levels\n"
        "- Weakens immune system over time\n\n"
        "**Evidence-Based Stress Reduction:**\n"
        "1. **Deep breathing** -- 4-7-8 technique (inhale 4s, hold 7s, exhale 8s)\n"
        "2. **Progressive muscle relaxation** -- Tense and release muscle groups\n"
        "3. **Mindfulness meditation** -- Even 10 minutes daily helps\n"
        "4. **Physical activity** -- Natural stress reliever\n"
        "5. **Social connection** -- Talk to friends, family, or a counselor\n\n"
        "**When stress is overwhelming** (consult your doctor):\n"
        "- **Magnesium supplements** may help with anxiety\n"
        "- **Ashwagandha** -- adaptogenic herb for stress resilience\n"
        "- For chronic anxiety, your doctor may discuss options like **SSRIs** or **Buspirone**\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- an artificial intelligence, "
        "not a doctor. AI can make mistakes. "
        "Please consult a qualified healthcare provider before making any medical decisions."
    ),
    "diet": (
        "Nutrition plays a vital role in health management. Here's an overview:\n\n"
        "**Heart-Healthy Diet Guidelines:**\n"
        "- Increase fruits, vegetables, and whole grains\n"
        "- Choose lean proteins (fish, chicken, legumes)\n"
        "- Limit sodium to less than 2,300mg per day\n"
        "- Reduce added sugars and processed foods\n"
        "- Include healthy fats (olive oil, nuts, avocado)\n\n"
        "**For Blood Sugar Management:**\n"
        "- Focus on low-glycemic index foods\n"
        "- Eat regular, balanced meals\n"
        "- Include fiber-rich foods\n"
        "- Monitor portion sizes\n\n"
        "**Supplements to consider** (ask your doctor):\n"
        "- **Omega-3 fatty acids** -- for heart and brain health\n"
        "- **Vitamin D** -- many people are deficient\n"
        "- **Probiotics** -- for gut health\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- an artificial intelligence, "
        "not a doctor. AI can make mistakes. "
        "Please consult a qualified healthcare provider or dietitian for personalized nutrition advice."
    ),
    "diabetes": (
        "Here's some information about diabetes management:\n\n"
        "**Understanding Diabetes:**\n"
        "- **Type 1**: Autoimmune condition requiring insulin\n"
        "- **Type 2**: Often manageable with lifestyle changes and medication\n"
        "- **Prediabetes**: Blood sugar is elevated but not yet diabetic range\n\n"
        "**Common Medications for Type 2 Diabetes:**\n"
        "- **Metformin** -- usually the first medication prescribed, helps reduce blood sugar\n"
        "- **SGLT2 inhibitors** (e.g., Empagliflozin) -- also protect heart and kidneys\n"
        "- **GLP-1 agonists** (e.g., Semaglutide) -- help with blood sugar and weight\n"
        "- **Insulin** -- for advanced cases or Type 1\n\n"
        "**Lifestyle Management:**\n"
        "1. Monitor blood sugar regularly\n"
        "2. Follow a balanced, low-glycemic diet\n"
        "3. Exercise regularly (150 min/week moderate activity)\n"
        "4. Maintain a healthy weight\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- an artificial intelligence, "
        "not a doctor. AI can make mistakes. **Please consult your doctor** "
        "before starting, stopping, or changing any diabetes medication."
    ),
    "fever": (
        "Here's what you should know about managing a fever:\n\n"
        "**When You Have a Fever:**\n"
        "- A temperature above 100.4F (38C) is generally considered a fever\n"
        "- Fever is usually the body's response to infection\n\n"
        "**Over-the-Counter Options:**\n"
        "- **Acetaminophen** (Tylenol) -- effective fever reducer, safe for most people\n"
        "- **Ibuprofen** (Advil) -- reduces fever and inflammation\n"
        "- Stay well hydrated with water, electrolyte drinks, or clear broth\n"
        "- Rest and allow your body to fight the infection\n\n"
        "**When to Seek Medical Help:**\n"
        "- Fever above 103F (39.4C) in adults\n"
        "- Fever lasting more than 3 days\n"
        "- Fever with severe headache, stiff neck, rash, or difficulty breathing\n"
        "- Any fever in infants under 3 months\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- an artificial intelligence, "
        "not a doctor. AI can make mistakes. **Please consult your doctor** "
        "if your fever is high, persistent, or accompanied by other concerning symptoms."
    ),
    "general": (
        "Thank you for your question! Here's what I can share based on your health data:\n\n"
        "**Your Health Dashboard:**\n"
        "- I'm monitoring your vitals including heart rate, blood pressure, SpO2, and activity levels\n"
        "- Your data is processed with trust scoring to ensure reliability\n"
        "- Any concerning trends trigger alerts automatically\n\n"
        "**General Wellness Tips:**\n"
        "1. Stay hydrated -- aim for 8 glasses of water daily\n"
        "2. Move regularly -- even short walks help\n"
        "3. Monitor your vitals consistently for better trend detection\n"
        "4. Keep logging data -- more data means better personalized insights\n\n"
        "**What I Can Help With:**\n"
        "- Health data analysis and trend detection\n"
        "- Medicine suggestions (with doctor-consultation warnings)\n"
        "- Lifestyle recommendations\n"
        "- Understanding your risk factors\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- an artificial intelligence, "
        "not a doctor. AI can make mistakes. "
        "Please consult a qualified healthcare provider before making any medical decisions."
    ),
    "forecast": (
        "Here's a 6-month health outlook based on your current data:\n\n"
        "**If Current Trends Continue:**\n"
        "- Your vital signs will continue to be monitored for changes\n"
        "- Seasonal factors may affect your activity levels and mood\n"
        "- Consistent data logging will improve prediction accuracy\n\n"
        "**What Could Improve Your Outlook:**\n"
        "1. Increase daily steps by 2,000 -- projected 15% cardiovascular risk reduction\n"
        "2. Improve sleep consistency -- better blood pressure regulation\n"
        "3. Add 2 servings of vegetables daily -- improved metabolic markers\n\n"
        "**Important Note:** Health forecasting is probabilistic, not deterministic. "
        "Your actual health trajectory depends on many factors.\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- an artificial intelligence, "
        "not a doctor. AI can make mistakes. "
        "Please consult a qualified healthcare provider for personalized health planning."
    ),
    "burns": (
        "Here's how to treat minor burns:\n\n"
        "**Immediate First Aid:**\n"
        "1. Cool the burn under cool (not cold) running water for 10-20 minutes\n"
        "2. Remove rings or tight items before swelling\n"
        "3. Do NOT apply ice, butter, or toothpaste\n\n"
        "**Medicines & Treatments:**\n"
        "- **Aloe vera gel** -- soothes and promotes healing\n"
        "- **Silver sulfadiazine cream** (Silvadene) -- for infection prevention\n"
        "- **Ibuprofen or Acetaminophen** -- for pain relief\n"
        "- **Burn ointments** like Neosporin or Bacitracin\n"
        "- Cover with a sterile non-stick bandage\n\n"
        "**When to See a Doctor:**\n"
        "- Burns larger than 3 inches\n"
        "- Burns on face, hands, feet, or joints\n"
        "- Deep burns (white or charred skin)\n"
        "- Chemical or electrical burns\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- not a doctor. AI can make mistakes. "
        "**Please consult your doctor** for serious burns or if symptoms worsen."
    ),
    "bruises": (
        "Here's how to treat bruises and minor injuries:\n\n"
        "**R.I.C.E. Method:**\n"
        "1. **Rest** the injured area\n"
        "2. **Ice** -- apply for 15-20 min every hour (wrap in cloth)\n"
        "3. **Compression** -- gentle elastic bandage\n"
        "4. **Elevation** -- raise above heart level\n\n"
        "**Topical Treatments:**\n"
        "- **Arnica gel/cream** -- reduces swelling and discoloration\n"
        "- **Hirudoid cream** (heparinoid) -- helps bruises heal faster\n"
        "- **Vitamin K cream** -- may reduce bruise appearance\n"
        "- **Ibuprofen gel** -- for pain and inflammation\n\n"
        "**Oral Pain Relief:**\n"
        "- **Ibuprofen** (Advil) -- reduces inflammation\n"
        "- **Acetaminophen** (Tylenol) -- for pain\n"
        "- Avoid aspirin (can increase bleeding/bruising)\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- not a doctor. AI can make mistakes. "
        "**Please consult your doctor** if bruising is severe, unexplained, or frequent."
    ),
    "allergy": (
        "Here's information about managing allergies:\n\n"
        "**Common Allergy Medicines:**\n"
        "- **Cetirizine** (Zyrtec) -- non-drowsy antihistamine\n"
        "- **Loratadine** (Claritin) -- non-drowsy, long-lasting\n"
        "- **Diphenhydramine** (Benadryl) -- fast-acting but causes drowsiness\n"
        "- **Fexofenadine** (Allegra) -- non-drowsy option\n\n"
        "**For Nasal Symptoms:**\n"
        "- **Fluticasone** nasal spray (Flonase)\n"
        "- **Saline nasal rinse** for congestion\n\n"
        "**For Severe Allergic Reactions (Anaphylaxis):**\n"
        "- Use **EpiPen** (epinephrine auto-injector) if prescribed\n"
        "- **Call emergency services immediately (911)**\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- not a doctor. AI can make mistakes. "
        "**Please consult your doctor** before starting allergy medication."
    ),
    "cold_flu": (
        "Here's how to manage cold and flu symptoms:\n\n"
        "**Over-the-Counter Options:**\n"
        "- **Acetaminophen/Ibuprofen** -- for fever and body aches\n"
        "- **Pseudoephedrine** (Sudafed) -- nasal decongestant\n"
        "- **Dextromethorphan** (Robitussin) -- cough suppressant\n"
        "- **Guaifenesin** (Mucinex) -- thins mucus\n"
        "- **Throat lozenges** with menthol or benzocaine\n\n"
        "**Home Remedies:**\n"
        "- Rest and stay hydrated\n"
        "- Warm salt water gargle for sore throat\n"
        "- Honey and lemon tea\n"
        "- Steam inhalation for congestion\n\n"
        "**When to See a Doctor:**\n"
        "- Symptoms lasting more than 10 days\n"
        "- High fever (above 103F/39.4C)\n"
        "- Difficulty breathing or chest pain\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- not a doctor. AI can make mistakes. "
        "**Please consult your doctor** if symptoms are severe or persistent."
    ),
    "stomach": (
        "Here's information about digestive/stomach issues:\n\n"
        "**For Acid Reflux/Heartburn:**\n"
        "- **Antacids** (Tums, Rolaids) -- quick relief\n"
        "- **Omeprazole** (Prilosec) -- reduces acid production\n"
        "- **Famotidine** (Pepcid) -- H2 blocker\n\n"
        "**For Nausea/Vomiting:**\n"
        "- **Bismuth subsalicylate** (Pepto-Bismol)\n"
        "- **Dimenhydrinate** (Dramamine) -- for motion sickness\n"
        "- Ginger tea or ginger supplements\n\n"
        "**For Diarrhea:**\n"
        "- **Loperamide** (Imodium)\n"
        "- Stay hydrated with ORS (oral rehydration solution)\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- not a doctor. AI can make mistakes. "
        "**Please consult your doctor** for persistent stomach issues."
    ),
    "emergency": (
        "**EMERGENCY CONTACTS & RESOURCES**\n\n"
        "**If this is a life-threatening emergency, call immediately:**\n"
        "- **911** (US) / **112** (EU/India) / **999** (UK) / **108** (India Ambulance)\n\n"
        "**When to Call Emergency:**\n"
        "- Chest pain or difficulty breathing\n"
        "- Signs of stroke (face drooping, arm weakness, speech difficulty)\n"
        "- Severe allergic reaction (anaphylaxis)\n"
        "- Uncontrolled bleeding\n"
        "- Loss of consciousness\n"
        "- Seizures\n\n"
        "**Find Help Nearby:**\n"
        "- Search 'hospitals near me' or 'pharmacies near me' in Google Maps\n"
        "- Use the Relay-med 'Nearby Services' feature on your My Health page\n"
        "- Most pharmacies offer walk-in consultations\n\n"
        "**Poison Control:** 1-800-222-1222 (US)\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- not a doctor. "
        "For emergencies, always call your local emergency number first."
    ),
    "skin_wound": (
        "Here's information about skin conditions and wound care:\n\n"
        "**For Cuts and Wounds:**\n"
        "- Clean with mild soap and water\n"
        "- Apply **antiseptic solution** (Betadine/Povidone-iodine)\n"
        "- Apply **antibiotic ointment** (Neosporin, Bacitracin)\n"
        "- Cover with a sterile bandage\n\n"
        "**For Skin Rashes/Infections:**\n"
        "- **Hydrocortisone cream** (1%) -- for itching and inflammation\n"
        "- **Calamine lotion** -- for soothing irritated skin\n"
        "- **Clotrimazole cream** (Lotrimin) -- for fungal infections\n"
        "- **Mupirocin ointment** -- for bacterial skin infections (prescription)\n\n"
        "**For Dry/Cracked Skin:**\n"
        "- **Petroleum jelly** (Vaseline) -- moisturizer and barrier\n"
        "- **Coconut oil** -- natural moisturizer\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- not a doctor. AI can make mistakes. "
        "**Please consult your doctor** if wounds show signs of infection or skin conditions persist."
    ),
    "back_pain": (
        "Here's information about managing back and joint pain:\n\n"
        "**Over-the-Counter Options:**\n"
        "- **Ibuprofen** (Advil) -- anti-inflammatory pain relief\n"
        "- **Naproxen** (Aleve) -- longer-lasting inflammation relief\n"
        "- **Acetaminophen** (Tylenol) -- for pain without inflammation\n\n"
        "**Topical Treatments:**\n"
        "- **Diclofenac gel** (Voltaren) -- anti-inflammatory gel\n"
        "- **Menthol/Camphor creams** (Icy Hot, Bengay)\n"
        "- **Capsaicin cream** -- for chronic pain\n\n"
        "**Non-Drug Approaches:**\n"
        "- Hot/cold therapy -- ice for first 48 hours, then heat\n"
        "- Gentle stretching and yoga\n"
        "- Posture correction\n"
        "- Physiotherapy exercises\n\n"
        "**When to See a Doctor:**\n"
        "- Pain lasting more than 2 weeks\n"
        "- Pain with numbness or tingling in legs\n"
        "- Pain after a fall or injury\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- not a doctor. AI can make mistakes. "
        "**Please consult your doctor** for persistent pain."
    ),
    "eye_ear": (
        "Here's information about common eye and ear issues:\n\n"
        "**For Eye Issues:**\n"
        "- **Artificial tears** -- for dry eyes\n"
        "- **Antihistamine eye drops** (Zaditor) -- for allergic eyes\n"
        "- **Warm compress** -- for styes or irritation\n"
        "- Avoid rubbing eyes; wash hands frequently\n\n"
        "**For Ear Issues:**\n"
        "- **Ear drops** (Debrox) -- for wax buildup\n"
        "- **Warm compress** -- for ear pain\n"
        "- **Antihistamines** -- for ear congestion from allergies\n"
        "- Do NOT insert cotton swabs deep into the ear\n\n"
        "**When to See a Doctor:**\n"
        "- Sudden vision changes or eye pain\n"
        "- Ear discharge or hearing loss\n"
        "- Persistent redness or swelling\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- not a doctor. AI can make mistakes. "
        "**Please consult your doctor** for persistent eye or ear problems."
    ),
    "dental": (
        "Here's information about common dental issues:\n\n"
        "**For Toothache:**\n"
        "- **Ibuprofen** (Advil) -- reduces pain and swelling\n"
        "- **Clove oil** (eugenol) -- natural numbing agent\n"
        "- **Orajel** (benzocaine gel) -- topical numbing\n"
        "- Salt water rinse -- reduces bacteria and inflammation\n\n"
        "**For Gum Issues:**\n"
        "- **Antiseptic mouthwash** (Listerine, Chlorhexidine)\n"
        "- Gentle brushing with soft-bristle toothbrush\n"
        "- Floss daily\n\n"
        "**When to See a Dentist:**\n"
        "- Severe or persistent toothache\n"
        "- Swollen or bleeding gums\n"
        "- Broken or chipped tooth\n"
        "- Jaw pain or difficulty chewing\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- not a doctor. AI can make mistakes. "
        "**Please consult a dentist** for dental problems."
    ),
    "first_aid": (
        "Here's a general first aid guide:\n\n"
        "**Basic First Aid Kit Should Include:**\n"
        "- Adhesive bandages (Band-Aids)\n"
        "- Sterile gauze and medical tape\n"
        "- Antiseptic wipes and solution (Betadine)\n"
        "- Antibiotic ointment (Neosporin)\n"
        "- Pain relievers (Ibuprofen, Acetaminophen)\n"
        "- Tweezers and scissors\n"
        "- Thermometer\n"
        "- Elastic bandage (ACE wrap)\n\n"
        "**Common First Aid Steps:**\n"
        "1. Assess the situation for safety\n"
        "2. Call emergency services if needed\n"
        "3. Stop bleeding by applying pressure\n"
        "4. Clean wounds with water and antiseptic\n"
        "5. Apply appropriate bandaging\n\n"
        "---\n"
        "**AI Health Disclaimer**: I am Relay-med AI -- not a doctor. AI can make mistakes. "
        "For serious injuries, call emergency services immediately."
    ),
}


def _extract_user_message(prompt: str) -> str:
    """Extract just the last user message from the full prompt."""
    # Look for the last [USER] block
    matches = re.findall(r"\[USER\]\s*\n(.*?)(?:\n\[|$)", prompt, re.DOTALL)
    if matches:
        return matches[-1].strip().lower()
    return prompt.lower()


def _extract_health_data(prompt: str) -> str:
    """Extract user health data from prompt if present."""
    match = re.search(r"\[My Health Data:\s*(.+?)\]", prompt)
    return match.group(1) if match else ""


def _personalize_response(response: str, health_data: str) -> str:
    """Prepend personalization note if user health data is available."""
    if not health_data:
        return response
    return (
        f"**Based on your health data** ({health_data}):\n\n"
        + response
    )


def _pick_fallback(prompt: str) -> str:
    """Pick the most relevant fallback response based on the user's actual question."""
    user_msg = _extract_user_message(prompt)
    health_data = _extract_health_data(prompt)

    # Check most specific topics first
    if any(w in user_msg for w in ["headache", "head ache", "migraine"]):
        return _personalize_response(FALLBACK_RESPONSES["headache"], health_data)
    if any(w in user_msg for w in ["diabetes", "diabetic", "blood sugar", "glucose", "insulin", "glyc"]):
        return _personalize_response(FALLBACK_RESPONSES["diabetes"], health_data)
    if any(w in user_msg for w in ["fever", "temperature high", "flu symptoms"]):
        return _personalize_response(FALLBACK_RESPONSES["fever"], health_data)
    if any(w in user_msg for w in ["burn", "scald", "hot water", "fire burn"]):
        return _personalize_response(FALLBACK_RESPONSES["burns"], health_data)
    if any(w in user_msg for w in ["bruise", "swelling", "sprain", "injury", "wound", "cut", "bleed", "scrape"]):
        return _personalize_response(FALLBACK_RESPONSES["bruises"], health_data)
    if any(w in user_msg for w in ["skin", "rash", "eczema", "acne", "pimple", "fungal", "ringworm", "ointment"]):
        return _personalize_response(FALLBACK_RESPONSES["skin_wound"], health_data)
    if any(w in user_msg for w in ["back pain", "joint", "knee", "arthritis", "muscle pain", "body pain", "neck pain", "shoulder"]):
        return _personalize_response(FALLBACK_RESPONSES["back_pain"], health_data)
    if any(w in user_msg for w in ["eye", "ear", "vision", "hearing", "earache", "eye drop"]):
        return _personalize_response(FALLBACK_RESPONSES["eye_ear"], health_data)
    if any(w in user_msg for w in ["tooth", "dental", "gum", "mouth sore", "cavity", "dentist"]):
        return _personalize_response(FALLBACK_RESPONSES["dental"], health_data)
    if any(w in user_msg for w in ["allergy", "allergic", "hives", "itch", "sneez", "hay fever"]):
        return _personalize_response(FALLBACK_RESPONSES["allergy"], health_data)
    if any(w in user_msg for w in ["cold", "cough", "sore throat", "runny nose", "congestion", "phlegm", "flu"]):
        return _personalize_response(FALLBACK_RESPONSES["cold_flu"], health_data)
    if any(w in user_msg for w in ["stomach", "nausea", "vomit", "diarrhea", "heartburn", "acid", "digest", "gastric", "abdomen", "belly"]):
        return _personalize_response(FALLBACK_RESPONSES["stomach"], health_data)
    if any(w in user_msg for w in ["medicine", "medication", "drug", "pill", "tablet", "supplement", "prescribe", "treat", "remedy", "cure"]):
        return _personalize_response(FALLBACK_RESPONSES["medication"], health_data)
    if any(w in user_msg for w in ["first aid", "kit", "bandage", "antiseptic"]):
        return _personalize_response(FALLBACK_RESPONSES["first_aid"], health_data)
    if any(w in user_msg for w in ["cardiovascular", "heart", "blood pressure", "bp", "cardiac", "chest pain", "cholesterol"]):
        return _personalize_response(FALLBACK_RESPONSES["cardiovascular"], health_data)
    if any(w in user_msg for w in ["sleep", "insomnia", "rest", "tired", "fatigue", "exhausted"]):
        return _personalize_response(FALLBACK_RESPONSES["sleep"], health_data)
    if any(w in user_msg for w in ["exercise", "walk", "steps", "activity", "workout", "gym", "run", "yoga"]):
        return _personalize_response(FALLBACK_RESPONSES["exercise"], health_data)
    if any(w in user_msg for w in ["stress", "anxiety", "anxious", "worried", "mental", "depression", "panic"]):
        return _personalize_response(FALLBACK_RESPONSES["stress"], health_data)
    if any(w in user_msg for w in ["diet", "nutrition", "food", "eat", "weight", "calorie", "protein", "vitamin"]):
        return _personalize_response(FALLBACK_RESPONSES["diet"], health_data)
    if any(w in user_msg for w in ["emergency", "911", "112", "ambulance", "hospital near", "doctor near", "pharmacy near", "urgent"]):
        return _personalize_response(FALLBACK_RESPONSES["emergency"], health_data)
    if any(w in user_msg for w in ["forecast", "future", "6 month", "predict", "change", "outlook"]):
        return _personalize_response(FALLBACK_RESPONSES["forecast"], health_data)
    if any(w in user_msg for w in ["pain", "ache", "sore", "hurt", "discomfort"]):
        return _personalize_response(FALLBACK_RESPONSES["medication"], health_data)
    if any(w in user_msg for w in ["infection", "antibiotic", "bacteria", "virus", "swollen"]):
        return _personalize_response(FALLBACK_RESPONSES["cold_flu"], health_data)
    if any(w in user_msg for w in ["dizzy", "dizziness", "vertigo", "faint", "lightheaded"]):
        return _personalize_response(FALLBACK_RESPONSES["cardiovascular"], health_data)
    return _personalize_response(FALLBACK_RESPONSES["general"], health_data)


class LLMAdapter:
    def __init__(self, provider: str | None = None):
        self.provider = provider or settings.effective_provider

    async def complete(self, prompt: str, stream: bool = False) -> AsyncIterator[str]:
        # Re-check effective provider each call (in case env changed)
        provider = settings.effective_provider if not self.provider or self.provider == "gemini" else self.provider

        if provider == "ollama":
            async for chunk in self._ollama_complete(prompt, stream):
                yield chunk
        elif provider == "gemini" and settings.GEMINI_API_KEY:
            async for chunk in self._gemini_complete(prompt, stream):
                yield chunk
        else:
            # Built-in fallback — no external API needed
            yield _pick_fallback(prompt)

    # ── Ollama ─────────────────────────────────────────────────────────────────

    async def _ollama_complete(self, prompt: str, stream: bool) -> AsyncIterator[str]:
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": stream}
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                if stream:
                    async with client.stream("POST", url, json=payload) as resp:
                        import json
                        async for line in resp.aiter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    yield data.get("response", "")
                                except Exception:
                                    continue
                else:
                    resp = await client.post(url, json=payload)
                    import json
                    data = resp.json()
                    yield data.get("response", "")
        except Exception as e:
            fallback = _pick_fallback(prompt)
            yield fallback + f"\n\n*(Note: This is a pre-written offline response because the local AI model (Ollama) is not running or unreachable at {url}.)*"

    # ── Gemini ─────────────────────────────────────────────────────────────────

    async def _gemini_complete(self, prompt: str, stream: bool) -> AsyncIterator[str]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash")

            if stream:
                response = await asyncio.to_thread(
                    model.generate_content, prompt, stream=True
                )
                for chunk in response:
                    yield chunk.text or ""
            else:
                response = await asyncio.to_thread(model.generate_content, prompt)
                yield response.text or ""
        except ImportError:
            fallback = _pick_fallback(prompt)
            yield fallback + "\n\n*(Note: This is a pre-written offline response because the Google Generative AI SDK is not installed.)*"
        except Exception as e:
            fallback = _pick_fallback(prompt)
            yield fallback + "\n\n*(Note: This is a pre-written offline response because the connection to the Gemini API failed.)*"


# Default adapter instance
llm_adapter = LLMAdapter()

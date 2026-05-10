// mockData.js — Synthetic health data for all RelayMed pages

export const mockUser = {
  name: 'ABC',
  abhaId: 'ABHA-7823-4561-9012',
  avatar: null,
  lastSync: '2 hours ago',
  wearableConnected: true,
  medicationStreak: 14,
  nextCheckup: 'Jun 12, 2026',
  language: 'EN',
};

export const mockHealthScore = {
  score: 72,
  lastWeek: 68,
  trend: 'up',
  updatedAt: 'Today, 2:15 PM',
  confidence: 87,
};

export const mockRiskCards = [
  {
    id: 'cardio',
    title: 'Cardiometabolic',
    icon: '❤️',
    status: 'Elevated',
    statusLevel: 'warning',
    value: '68/100',
    trend: 'up',
    trendLabel: '+4 this week',
    lastUpdated: '1 hour ago',
    confidence: 82,
    sparkline: [55, 58, 61, 60, 65, 64, 68],
    detail: 'Resting heart rate slightly above baseline. BP trend stable.',
  },
  {
    id: 'renal',
    title: 'Renal Health',
    icon: '🫘',
    status: 'Normal',
    statusLevel: 'safe',
    value: '88/100',
    trend: 'stable',
    trendLabel: 'No change',
    lastUpdated: '3 days ago',
    confidence: 91,
    sparkline: [85, 86, 88, 87, 88, 89, 88],
    detail: 'Hydration levels and kidney function markers within range.',
  },
  {
    id: 'sleep',
    title: 'Sleep & Mental',
    icon: '🧠',
    status: 'Worth Checking',
    statusLevel: 'warning',
    value: '59/100',
    trend: 'down',
    trendLabel: '-6 this week',
    lastUpdated: '8 hours ago',
    confidence: 76,
    sparkline: [70, 68, 65, 62, 60, 61, 59],
    detail: 'Sleep consistency dropped. Average 5.2 hrs vs recommended 7–8.',
  },
  {
    id: 'respiratory',
    title: 'Respiratory',
    icon: '🫁',
    status: 'Normal',
    statusLevel: 'safe',
    value: '91/100',
    trend: 'up',
    trendLabel: '+2 this week',
    lastUpdated: '4 hours ago',
    confidence: 94,
    sparkline: [88, 89, 90, 89, 91, 90, 91],
    detail: 'SpO2 readings consistently above 97%. No anomalies detected.',
  },
];

export const mockAlerts = [
  {
    id: 'alert-1',
    signal: 'Sleep Consistency',
    severity: 'warning',
    why: 'Your average sleep duration dropped below 6 hours for 4 consecutive nights. This pattern correlates with increased cardiometabolic risk signals.',
    action: 'Consider maintaining a consistent sleep schedule. A 30-min improvement could shift your score by +8 points.',
    confidence: 76,
    counterfactual: 'Your score drops 22 points if sleep consistency continues declining.',
    time: '8 hours ago',
    dismissed: false,
  },
  {
    id: 'alert-2',
    signal: 'Resting Heart Rate',
    severity: 'info',
    why: 'Resting HR averaged 82 bpm over 3 days — slightly above your personal baseline of 74 bpm.',
    action: 'Consider a checkup if this trend persists beyond 7 days. Stress or dehydration are common causes.',
    confidence: 68,
    counterfactual: 'Improving hydration alone may reduce this signal by 40%.',
    time: '1 hour ago',
    dismissed: false,
  },
];

export const mockTimeline = [
  { date: 'May 9', event: 'Wearable synced — HR elevated signal', type: 'warning' },
  { date: 'May 7', event: 'Lab report processed — Renal markers normal', type: 'success' },
  { date: 'May 5', event: 'Sleep score dropped below 60', type: 'warning' },
  { date: 'Apr 28', event: 'Health score improved to 72 (+4)', type: 'success' },
  { date: 'Apr 20', event: 'ABDM connected — 3 sources synced', type: 'info' },
  { date: 'Apr 15', event: 'Medication adherence streak started', type: 'success' },
  { date: 'Apr 10', event: 'Annual checkup reminder sent', type: 'info' },
  { date: 'Mar 30', event: 'Respiratory anomaly detected — resolved', type: 'danger' },
];

export const mockFamily = [
  {
    id: 'fam-1',
    name: 'Rajesh Sharma',
    relation: 'Father',
    age: 56,
    healthScore: 58,
    lastSync: '3 hours ago',
    alerts: 2,
    signals: [
      { label: 'Cardio', status: 'warning', icon: '❤️' },
      { label: 'Sleep', status: 'warning', icon: '🧠' },
      { label: 'Renal', status: 'safe', icon: '🫘' },
    ],
    sharedRisks: ['Cardiometabolic', 'Sleep Quality'],
  },
  {
    id: 'fam-2',
    name: 'Priya Sharma',
    relation: 'Mother',
    age: 51,
    healthScore: 79,
    lastSync: '1 day ago',
    alerts: 0,
    signals: [
      { label: 'Cardio', status: 'safe', icon: '❤️' },
      { label: 'Sleep', status: 'safe', icon: '🧠' },
      { label: 'Renal', status: 'safe', icon: '🫘' },
    ],
    sharedRisks: [],
  },
  {
    id: 'fam-3',
    name: 'Arjun Sharma',
    relation: 'Brother',
    age: 24,
    healthScore: 88,
    lastSync: '5 minutes ago',
    alerts: 0,
    signals: [
      { label: 'Cardio', status: 'safe', icon: '❤️' },
      { label: 'Respiratory', status: 'safe', icon: '🫁' },
      { label: 'Sleep', status: 'warning', icon: '🧠' },
    ],
    sharedRisks: ['Sleep Quality'],
  },
];

export const mockConnectedSources = [
  { name: 'ABDM / ABHA', status: 'connected', trust: 'HIGH', lastSync: '2 hours ago', icon: '🏥', records: 47 },
  { name: 'Apple Health', status: 'connected', trust: 'MEDIUM', lastSync: '8 hours ago', icon: '🍎', records: 1240 },
  { name: 'Google Fit', status: 'disconnected', trust: 'MEDIUM', lastSync: 'Never', icon: '🔵', records: 0 },
  { name: 'Fitbit', status: 'connected', trust: 'MEDIUM', lastSync: '1 day ago', icon: '⌚', records: 892 },
  { name: 'Manual Upload', status: 'available', trust: 'LOW', lastSync: '3 days ago', icon: '📁', records: 8 },
];

export const mockTrajectoryData = {
  baseline: [72, 72, 72, 72, 72, 72],
  projected3m: [72, 74, 76, 78, 80, 82],
  projected6m: [72, 75, 78, 81, 84, 87],
  labels: ['Now', 'Month 1', 'Month 2', 'Month 3', 'Month 4', 'Month 5', 'Month 6'],
};

export const mockWeeklyBrief = {
  week: 'May 5 – May 11, 2026',
  improved: ['Respiratory score up 3 points', 'Medication adherence 100%', 'Renal markers stable'],
  attention: ['Sleep consistency declined', 'Resting heart rate slightly elevated'],
  keyAction: 'Set a fixed sleep schedule — 10:30 PM to 6:30 AM — for the next 7 days.',
  scoreChange: +4,
  lastWeekScore: 68,
  thisWeekScore: 72,
};

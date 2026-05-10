import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { RelayMedLogo } from './Logo';
import {
  LayoutDashboard, Users, TrendingUp, FileText, MessageSquare,
  Settings, LogOut, Menu, X, Bell, Wifi, WifiOff
} from 'lucide-react';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/family', icon: Users, label: 'Family Guardian' },
  { to: '/simulator', icon: TrendingUp, label: 'Trajectory' },
  { to: '/reports', icon: FileText, label: 'Reports & Data' },
  { to: '/chat', icon: MessageSquare, label: 'AI Assistant' },
];

const LANGUAGES = ['EN', 'हिं', 'ಕನ್ನಡ', 'தமிழ்', 'తెలుగు'];

export default function AppShell({ children, user }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [lang, setLang] = useState('EN');
  const [isOnline] = useState(true);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('relaymed_auth');
    navigate('/login');
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0A0F1E', position: 'relative' }}>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 40 }}
        />
      )}

      {/* Sidebar */}
      <aside style={{
        position: 'fixed', top: 0, left: 0, height: '100vh', width: 240,
        background: '#0D1527', borderRight: '1px solid #1F2937',
        display: 'flex', flexDirection: 'column', zIndex: 50,
        transform: sidebarOpen ? 'translateX(0)' : undefined,
        transition: 'transform 0.3s ease',
      }}
        className="hidden-mobile"
      >
        {/* Logo */}
        <div style={{ padding: '24px 20px', borderBottom: '1px solid #1F2937' }}>
          <RelayMedLogo />
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: 4 }}>
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              style={({ isActive }) => ({
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 14px', borderRadius: 10, textDecoration: 'none',
                color: isActive ? '#00D4FF' : '#9CA3AF',
                background: isActive ? 'rgba(0, 212, 255, 0.08)' : 'transparent',
                border: isActive ? '1px solid rgba(0,212,255,0.2)' : '1px solid transparent',
                transition: 'all 0.2s',
                fontFamily: 'DM Sans, sans-serif',
                fontWeight: 500, fontSize: 14,
              })}
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Bottom */}
        <div style={{ padding: '16px 12px', borderTop: '1px solid #1F2937', display: 'flex', flexDirection: 'column', gap: 4 }}>
          <NavLink to="/settings" style={{ display:'flex',alignItems:'center',gap:12,padding:'10px 14px',borderRadius:10,
            textDecoration:'none',color:'#9CA3AF',fontFamily:'DM Sans,sans-serif',fontSize:14,
            transition:'all 0.2s' }}>
            <Settings size={18} />Settings
          </NavLink>
          <button onClick={handleLogout} style={{ display:'flex',alignItems:'center',gap:12,padding:'10px 14px',
            borderRadius:10,background:'transparent',border:'none',color:'#6B7280',cursor:'pointer',
            fontFamily:'DM Sans,sans-serif',fontSize:14,width:'100%',textAlign:'left',transition:'all 0.2s' }}>
            <LogOut size={18} />Sign Out
          </button>
        </div>
      </aside>

      {/* Mobile sidebar */}
      <aside style={{
        position: 'fixed', top: 0, left: 0, height: '100vh', width: 260,
        background: '#0D1527', borderRight: '1px solid #1F2937',
        display: 'flex', flexDirection: 'column', zIndex: 51,
        transform: sidebarOpen ? 'translateX(0)' : 'translateX(-100%)',
        transition: 'transform 0.3s ease',
      }} className="mobile-sidebar">
        <div style={{ padding: '20px', borderBottom: '1px solid #1F2937', display:'flex',justifyContent:'space-between',alignItems:'center' }}>
          <RelayMedLogo size="sm" />
          <button onClick={() => setSidebarOpen(false)} style={{ background:'none',border:'none',color:'#9CA3AF',cursor:'pointer' }}>
            <X size={20} />
          </button>
        </div>
        <nav style={{ flex:1,padding:'16px 12px',display:'flex',flexDirection:'column',gap:4 }}>
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} onClick={() => setSidebarOpen(false)}
              style={({ isActive }) => ({
                display:'flex',alignItems:'center',gap:12,padding:'10px 14px',borderRadius:10,textDecoration:'none',
                color:isActive?'#00D4FF':'#9CA3AF',
                background:isActive?'rgba(0,212,255,0.08)':'transparent',
                border:isActive?'1px solid rgba(0,212,255,0.2)':'1px solid transparent',
                fontFamily:'DM Sans,sans-serif',fontWeight:500,fontSize:14,
              })}>
              <Icon size={18} />{label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <div style={{ flex: 1, marginLeft: 240, display: 'flex', flexDirection: 'column', minHeight: '100vh' }}
        className="main-content">

        {/* Offline Banner */}
        {!isOnline && (
          <div style={{ background:'rgba(245,158,11,0.1)',borderBottom:'1px solid rgba(245,158,11,0.3)',
            padding:'8px 24px',display:'flex',alignItems:'center',gap:8,fontSize:13,color:'#F59E0B',fontFamily:'DM Sans,sans-serif' }}>
            <WifiOff size={14} />
            <span>Offline mode — last synced {user?.lastSync || '2 hours ago'}. Core features still available.</span>
          </div>
        )}

        {/* Top Bar */}
        <header style={{ padding:'16px 28px',borderBottom:'1px solid #1F2937',background:'rgba(13,21,39,0.8)',
          backdropFilter:'blur(12px)',display:'flex',alignItems:'center',justifyContent:'space-between',
          position:'sticky',top:0,zIndex:30 }}>
          <button onClick={() => setSidebarOpen(true)} className="mobile-menu-btn"
            style={{ background:'none',border:'none',color:'#9CA3AF',cursor:'pointer',display:'none' }}>
            <Menu size={22} />
          </button>

          <div style={{ display:'flex',alignItems:'center',gap:8 }}>
            {isOnline && (
              <div style={{ display:'flex',alignItems:'center',gap:6,fontSize:12,color:'#10B981' }}>
                <div style={{ width:7,height:7,borderRadius:'50%',background:'#10B981',
                  boxShadow:'0 0 6px #10B981',animation:'pulse 2s infinite' }} />
                Live
              </div>
            )}
          </div>

          <div style={{ display:'flex',alignItems:'center',gap:16 }}>
            {/* Language switcher */}
            <div style={{ display:'flex',alignItems:'center',gap:4 }}>
              {LANGUAGES.map(l => (
                <button key={l} onClick={() => setLang(l)} style={{
                  background: lang===l ? 'rgba(0,212,255,0.1)' : 'transparent',
                  border: lang===l ? '1px solid rgba(0,212,255,0.3)' : '1px solid transparent',
                  color: lang===l ? '#00D4FF' : '#6B7280',
                  padding:'3px 8px',borderRadius:6,cursor:'pointer',fontSize:11,
                  fontFamily:'DM Sans,sans-serif',transition:'all 0.2s',
                }}>
                  {l}
                </button>
              ))}
            </div>

            {/* Notifications */}
            <button style={{ background:'rgba(255,255,255,0.04)',border:'1px solid #1F2937',
              borderRadius:10,padding:'8px',color:'#9CA3AF',cursor:'pointer',position:'relative',display:'flex' }}>
              <Bell size={18} />
              <span style={{ position:'absolute',top:-4,right:-4,background:'#EF4444',
                color:'white',borderRadius:'50%',width:16,height:16,fontSize:10,
                display:'flex',alignItems:'center',justifyContent:'center',fontWeight:700 }}>2</span>
            </button>

            {/* Avatar */}
            <div style={{ width:36,height:36,borderRadius:'50%',
              background:'linear-gradient(135deg,#00D4FF,#7C3AED)',
              display:'flex',alignItems:'center',justifyContent:'center',
              fontSize:14,fontWeight:700,color:'white',cursor:'pointer',
              boxShadow:'0 0 12px rgba(0,212,255,0.3)' }}>
              {user?.name?.charAt(0) || 'A'}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main style={{ flex:1,padding:'28px',overflowY:'auto' }} className="page-enter">
          {children}
        </main>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .hidden-mobile { display: none !important; }
          .mobile-menu-btn { display: flex !important; }
          .main-content { margin-left: 0 !important; }
        }
        @keyframes pulse {
          0%,100% { opacity:1; }
          50% { opacity:0.4; }
        }
      `}</style>
    </div>
  );
}

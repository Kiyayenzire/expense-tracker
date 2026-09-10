import React, { useEffect, useRef, useState } from 'react';

export function Header({ activePage, onNavigate, onLogout, onDeleteAccount, theme, setTheme, username = '', profilePicture = '', queuedCount = 0, isSyncing = false }) {
	const [menuOpen, setMenuOpen] = useState(false);
	const menuRef = useRef(null);

	const getInitials = (name) => {
		return name
			.split(' ')
			.map(word => word[0])
			.join('')
			.toUpperCase()
			.slice(0, 2);
	};

	const initials = getInitials(username || 'User');
	const displayPicture = profilePicture || null;

	useEffect(() => {
		const handleClickOutside = (event) => {
			if (menuRef.current && !menuRef.current.contains(event.target)) {
				setMenuOpen(false);
			}
		};

		document.addEventListener('mousedown', handleClickOutside);
		return () => document.removeEventListener('mousedown', handleClickOutside);
	}, []);

	return (
		<header className="header app-header">
			<div className="header-topline">
				<h1>Expense Tracker</h1>
				<p className="small-text">Today is {new Intl.DateTimeFormat('en-GB').format(new Date())}</p>
				<div className="header-tools">
					<div className="profile-menu-wrapper" ref={menuRef}>
						<button type="button" className="user-profile-section profile-button" aria-expanded={menuOpen} onClick={() => setMenuOpen((value) => !value)}>
							<div className="profile-picture" style={{ width: '3rem', height: '3rem', flex: '0 0 3rem', overflow: 'hidden', borderRadius: '50%' }}>
								{displayPicture ? (
									<img src={displayPicture} alt={username} title={username} style={{ display: 'block', width: '100%', height: '100%', objectFit: 'cover' }} />
								) : (
									<div className="profile-avatar" title={username}>
										{initials}
									</div>
								)}
							</div>
							<span className="username">{username || 'User'}</span>
							<span className="profile-chevron" aria-hidden="true">▾</span>
						</button>

						{menuOpen && (
							<div className="profile-dropdown-menu" role="menu" aria-label="Account menu">
								<div className="profile-dropdown-header">Account settings</div>
								<button type="button" className="profile-dropdown-item" onClick={() => { setMenuOpen(false); onNavigate && onNavigate('profile'); }}>
									Profile
								</button>
								{onDeleteAccount && (
									<button type="button" className="profile-dropdown-item danger-item" onClick={() => { setMenuOpen(false); onDeleteAccount(); }}>
										Delete account
									</button>
								)}
								<button type="button" className="profile-dropdown-item danger-item" onClick={() => { setMenuOpen(false); onLogout(); }}>
									Log out
								</button>
							</div>
						)}
					</div>

					{queuedCount > 0 && (
						<span className="badge bg-warning text-dark" title={`${queuedCount} item(s) queued for sync`}>
							⧖ {queuedCount}
						</span>
					)}
					{isSyncing && (
						<span className="badge bg-info text-white" title="Syncing expenses">
							⟳ Syncing
						</span>
					)}
					<label className="theme-selector" htmlFor="theme-selector">
						<span className="sr-only">Colour theme</span>
						<select id="theme-selector" value={theme} onChange={(event) => setTheme(event.target.value)}>
							<option value="light">Light</option>
							<option value="dark">Dark</option>
							<option value="green">Green</option>
							<option value="blue">Blue</option>
							<option value="red">Red</option>
							<option value="gold">Gold</option>
							<option value="silver">Silver</option>
						</select>
					</label>
				</div>
			</div>
			<nav className="nav-actions" aria-label="Main navigation">
				<button type="button" className={activePage === 'dashboard' ? 'nav-button active' : 'nav-button'} onClick={() => onNavigate('dashboard')}>Dashboard</button>
				<button type="button" className={activePage === 'add-expense' ? 'nav-button active' : 'nav-button'} onClick={() => onNavigate('add-expense')}>Add Expense</button>
				<button type="button" className={activePage === 'expenses' ? 'nav-button active' : 'nav-button'} onClick={() => onNavigate('expenses')}>Expenses</button>
				<button type="button" className={activePage === 'reports' ? 'nav-button active' : 'nav-button'} onClick={() => onNavigate('reports')}>Reports</button>
				<button type="button" className={activePage === 'insights' ? 'nav-button active' : 'nav-button'} onClick={() => onNavigate('insights')}>Insights</button>
			</nav>
		</header>
	);
}

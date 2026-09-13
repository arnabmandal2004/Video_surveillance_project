import { NavLink, Outlet } from "react-router-dom";

export default function Layout() {
    return (
        <div className="app-shell">
            <aside className="sidebar">
                <div className="brand">
                    <div className="brand-title">
                        SENTINEL AI
                    </div>

                    <div className="system-status">
                        <span className="status-dot" />
                        System Online
                    </div>
                </div>

                <nav className="sidebar-nav">
                    <NavLink
                        to="/dashboard"
                        className={({ isActive }) =>
                            `nav-item ${isActive ? "active" : ""}`
                        }
                    >
                        Dashboard
                    </NavLink>

                    <NavLink
                        to="/analysis"
                        className={({ isActive }) =>
                            `nav-item ${isActive ? "active" : ""}`
                        }
                    >
                        Video Analysis
                    </NavLink>

                    <NavLink
                        to="/live"
                        className={({ isActive }) =>
                            `nav-item ${isActive ? "active" : ""}`
                        }
                    >
                        Live Feeds
                    </NavLink>

                    <NavLink
                        to="/alerts"
                        className={({ isActive }) =>
                            `nav-item ${isActive ? "active" : ""}`
                        }
                    >
                        Alerts
                    </NavLink>

                    <NavLink
                        to="/events"
                        className={({ isActive }) =>
                            `nav-item ${isActive ? "active" : ""}`
                        }
                    >
                        Events
                    </NavLink>

                    <NavLink
                        to="/analytics"
                        className={({ isActive }) =>
                            `nav-item ${isActive ? "active" : ""}`
                        }
                    >
                        Analytics
                    </NavLink>

                    <NavLink
                        to="/reports"
                        className={({ isActive }) =>
                            `nav-item ${isActive ? "active" : ""}`
                        }
                    >
                        Reports
                    </NavLink>

                    <NavLink
                        to="/settings"
                        className={({ isActive }) =>
                            `nav-item ${isActive ? "active" : ""}`
                        }
                    >
                        Settings
                    </NavLink>
                </nav>
            </aside>

            <main className="main-content">
                <Outlet />
            </main>
        </div>
    );
}
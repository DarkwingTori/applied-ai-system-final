import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Advisor" },
  { to: "/schedule", label: "Schedule" },
];

export function Nav() {
  return (
    <header className="sticky top-0 z-10 border-b border-pawpal-border bg-white/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🐾</span>
          <span className="text-lg font-semibold text-pawpal-text">PawPal<span className="text-brand-500">+</span> AI</span>
        </div>
        <nav className="flex gap-1">
          {links.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end
              className={({ isActive }) =>
                `rounded-lg px-4 py-1.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-brand-500 text-white"
                    : "text-pawpal-muted hover:bg-brand-50 hover:text-brand-600"
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // PawPal+ design tokens — swap hex values with your Figma export
        brand: {
          50:  "#fdf4ef",
          100: "#fae4d2",
          200: "#f5c6a0",
          300: "#ee9f63",
          400: "#e67533",
          500: "#d95e1a",  // primary
          600: "#b84613",
          700: "#923511",
          800: "#762d14",
          900: "#612713",
        },
        pawpal: {
          bg:      "#fdf8f4",
          surface: "#ffffff",
          border:  "#f0e6dc",
          text:    "#1a1109",
          muted:   "#7a6050",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      borderRadius: {
        "2xl": "1.25rem",
      },
      boxShadow: {
        card: "0 2px 12px 0 rgba(0,0,0,0.08)",
      },
    },
  },
  plugins: [],
};


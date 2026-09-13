/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        workstation: {
          desktop: "#0f172a",
          dock: "#1e293b",
          window: "#0f172a",
          border: "#334155",
        }
      },
    },
  },
  plugins: [],
}

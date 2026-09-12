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
        slack: {
          sidebar: "#19171d",
          active: "#1164A3",
          hover: "#27242c",
          border: "#383540",
          mention: "#f2c744",
        },
      },
    },
  },
  plugins: [],
}

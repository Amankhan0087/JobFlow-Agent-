/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0A0F1E",
        surface: "#111827",
        border: "#1F2937",
        primary: "#2DD4BF",
        secondary: "#6366F1",
        text: "#F9FAFB",
        muted: "#6B7280",
      },
    },
  },
  plugins: [],
};

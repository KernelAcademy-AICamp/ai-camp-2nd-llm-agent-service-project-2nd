/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        accent: {
          DEFAULT: "#1ABC9C", // Primary CTA
          dark: "#16A085",
        },
        "semantic-error": "#E74C3C",
        "deep-trust-blue": "#2C3E50",
        "calm-grey": "#F8F9FA",
        "success-green": "#2ECC71",
      },
      fontFamily: {
        sans: ["var(--font-pretendard)", "sans-serif"],
      },
    },
  },
  plugins: [],
}

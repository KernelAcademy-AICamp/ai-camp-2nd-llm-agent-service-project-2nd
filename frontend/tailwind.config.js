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
      keyframes: {
        'border-beam': {
          '0%, 100%': {
            transform: 'translateX(-100%)',
          },
          '50%': {
            transform: 'translateX(100%)',
          },
        },
      },
      animation: {
        'border-beam': 'border-beam 3s linear infinite',
      },
    },
  },
  plugins: [],
}

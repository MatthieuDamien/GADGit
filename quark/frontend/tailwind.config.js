module.exports = {
  darkMode: 'class',
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Mapping des variables Radix pour une utilisation avec Tailwind
        // Exemple : bg-blue-1, text-gray-12, border-lime-7
        blue: {
          1: 'var(--blue-1)', 2: 'var(--blue-2)', 3: 'var(--blue-3)', 4: 'var(--blue-4)',
          5: 'var(--blue-5)', 6: 'var(--blue-6)', 7: 'var(--blue-7)', 8: 'var(--blue-8)',
          9: 'var(--blue-9)', 10: 'var(--blue-10)', 11: 'var(--blue-11)', 12: 'var(--blue-12)',
          contrast: 'var(--blue-contrast)', surface: 'var(--blue-surface)',
          indicator: 'var(--blue-indicator)', track: 'var(--blue-track)',
        },
        gray: {
          1: 'var(--gray-1)', 2: 'var(--gray-2)', 3: 'var(--gray-3)', 4: 'var(--gray-4)',
          5: 'var(--gray-5)', 6: 'var(--gray-6)', 7: 'var(--gray-7)', 8: 'var(--gray-8)',
          9: 'var(--gray-9)', 10: 'var(--gray-10)', 11: 'var(--gray-11)', 12: 'var(--gray-12)',
          contrast: 'var(--gray-contrast)', surface: 'var(--gray-surface)',
          indicator: 'var(--gray-indicator)', track: 'var(--gray-track)',
        },
        lime: {
          1: 'var(--lime-1)', 2: 'var(--lime-2)', 3: 'var(--lime-3)', 4: 'var(--lime-4)',
          5: 'var(--lime-5)', 6: 'var(--lime-6)', 7: 'var(--lime-7)', 8: 'var(--lime-8)',
          9: 'var(--lime-9)', 10: 'var(--lime-10)', 11: 'var(--lime-11)', 12: 'var(--lime-12)',
          contrast: 'var(--gray-contrast)', surface: 'var(--gray-surface)',
          indicator: 'var(--gray-indicator)', track: 'var(--gray-track)',
        },
        orange: {
          1: "var(--orange-1)", 2: "var(--orange-2)", 3: "var(--orange-3)", 4: "var(--orange-4)",
          5: "var(--orange-5)", 6: "var(--orange-6)", 7: "var(--orange-7)", 8: "var(--orange-8)",
          9: "var(--orange-9)", 10: "var(--orange-10)", 11: "var(--orange-11)", 12: "var(--orange-12)",
        },
        green: {
          1: "var(--green-1)", 2: "var(--green-2)", 3: "var(--green-3)", 4: "var(--green-4)",
          5: "var(--green-5)", 6: "var(--green-6)", 7: "var(--green-7)", 8: "var(--green-8)",
          9: "var(--green-9)", 10: "var(--green-10)", 11: "var(--green-11)", 12: "var(--green-12)",
        },
        yellow: {
          1: "var(--yellow-1)", 2: "var(--yellow-2)", 3: "var(--yellow-3)", 4: "var(--yellow-4)",
          5: "var(--yellow-5)", 6: "var(--yellow-6)", 7: "var(--yellow-7)", 8: "var(--yellow-8)",
          9: "var(--yellow-9)", 10: "var(--yellow-10)", 11: "var(--yellow-11)", 12: "var(--yellow-12)",
        },
        red: {
          1: 'var(--red-1)', 2: 'var(--red-2)', 3: 'var(--red-3)', 4: 'var(--red-4)',
          5: 'var(--red-5)', 6: 'var(--red-6)', 7: 'var(--red-7)', 8: 'var(--red-8)',
          9: 'var(--red-9)', 10: 'var(--red-10)', 11: 'var(--red-11)', 12: 'var(--red-12)',
        },
      }
    },
  },
  plugins: [],
}
module.exports = {
  darkMode: 'class',
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Couleurs pour le thème light/dark
        'primary': {
          light: '#004970', // bleu en light mode
          dark: '#AEC923',  // jaune en dark mode
        },
        'background': {
          light: '#FFFFFF',
          dark: '#000000',
        },
        'surface': {
          light: '#F8F9FA',
          dark: '#0A0A0A',
        },
        'border': {
          light: '#E2E4E9',
          dark: '#1A1A1A',
        },
        'neutral': '#8B8D98', // gris pour les deux modes
        
        // Couleurs originales conservées
        'jaune': {
          500:'#AEC923',
        },
        'marine': {
          100:'#0e2531',
          300:'#003c58',
          500:'#004970',
          600:'#006391',
          700:'#0080b7',
          800:'#009ee1',
        },
        'bordeaux': {
          500:'#8a0f22',
          600:'#db0026',
          800:'#e31937',
        }
      },
      backgroundColor: {
        'base': 'var(--bg-base)',
        'surface': 'var(--bg-surface)',
        'elevated': 'var(--bg-elevated)',
      },
      textColor: {
        'primary': 'var(--text-primary)',
        'secondary': 'var(--text-secondary)',
        'accent': 'var(--text-accent)',
      },
      borderColor: {
        'default': 'var(--border-default)',
      }
    },
  },
  plugins: [],
}
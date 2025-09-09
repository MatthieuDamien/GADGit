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
          bg100:'#000',   // Background
          bg200:'#101209',   // Background
          interactive300:'#202410',   // Composant interactif
          interactive400:'#2D3412',   // Composant interactif
          interactive500:'#394217',   // Composant interactif
          border600:'#46501C',   // Bordures et séparateurs
          border700:'#546020',   // Bordures et séparateurs
          border800:'#637223',   // Bordures et Focus ring (permet de savoir quel élément est sélectionné)
          main:'#AEC923',
          1000:'#AEC923',  // Couleur solide, boutons
          1100:'#A4BE04',  // Couleur solide, boutons
          text1200:'#A4BE04',  // Texte accessible (secondary text, links)
          text1300:'#E1F1AF',  // Texte accessible (High contrast)
        },
        'marine': {
          bg100:'#F8FEFF',   // Background
          bg200:'#F0FAFF',   // Background
          interactive300:'#DDF6FF',   // Composant interactif
          interactive400:'#CAEFFF',   // Composant interactif
          interactive500:'#B4E6FF',   // Composant interactif
          border600:'#9BD9FF',   // Bordures et séparateurs
          border700:'#7AC9FF',   // Bordures et séparateurs
          border800:'#4BB1F5',   // Bordures et Focus ring (permet de savoir quel élément est sélectionné)
          main:'#004970',
          1000:'#004970',  // Couleur solide, boutons
          1100:'#1B5A82',  // Couleur solide, boutons
          text1200:'#0072B1',  // Texte accessible (secondary text, links)
          text1300:'#003F65',  // Texte accessible (High contrast)
        },
        'bordeaux': {
          500:'#8a0f22',
          600:'#db0026',
          800:'#e31937',
        },   
        'gris': {
          300:'#1F1F22',
          400 : '#2C2C30',
          500 : '#393A3F',
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
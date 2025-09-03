pour init : 
```bash
cd GAD/GADGIT/quark
npm start
```

si c'est lancé : http://localhost:3000/

ne pas oublier d'installer les dépendances suivantes :
```bash
# Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Lucide React pour les icônes
npm install lucide-react
```

organisation :
```
src/ 
	components/ 
		common/ 
			Card.jsx 
			ProgressBar.jsx 
			Badge.jsx 
		dashboard/ 
			ResourceCard.jsx 
			QueueItem.jsx 
			ActiveTask.jsx 
			ErrorItem.jsx 
		layout/ 
			Header.jsx 
	pages/ 
		QuarkDashboard.jsx 
	utils/ 
		constants.js 
		helpers.js
```
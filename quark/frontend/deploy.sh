# https://www.youtube.com/watch?v=KFwFDZpEzXY 16:50

echo "Switching to branch master"
git checkout master

echo "Building app..."
yarn run build

echo "Deploying files to server..."
scp -r build/* #user@XXX.XXX.XXX.XXX:/var/www/XXX.XXX.XXX.XXX/
echo ""
echo "Deployment complete."
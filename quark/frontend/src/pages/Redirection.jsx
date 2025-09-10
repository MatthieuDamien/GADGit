import { useNavigate } from 'react-router-dom';

function Redirection() {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate('/home');
  };

  return <button onClick={handleClick}>Aller à l'accueil</button>;
}
import userAvatarSvg from '../assets/user-avatar.svg';
import agentAvatarSvg from '../assets/agent-avatar.svg';

export default function Avatar({ type = 'user', className = '' }) {
  const isUser = type === 'user';
  
  return (
    <div className={`avatar ${className}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
        isUser ? 'bg-primary text-primary-content' : 'bg-secondary text-secondary-content'
      }`}>
        <img
          src={isUser ? userAvatarSvg : agentAvatarSvg}
          alt={isUser ? 'User' : 'Assistant'}
          className="w-5 h-5"
        />
      </div>
    </div>
  );
}

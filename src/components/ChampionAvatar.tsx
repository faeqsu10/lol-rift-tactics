import type { CSSProperties } from 'react';
import type { CombatUnit } from '../game/types';

type AvatarUnit = Pick<CombatUnit, 'id' | 'accent' | 'team'>;
type AvatarSize = 'card' | 'battlefield' | 'spotlight';

function AvatarIllustration({ unit }: { unit: AvatarUnit }) {
  const gradientId = `${unit.id}-avatar-gradient`;
  const shadowColor = unit.team === 'blue' ? '#163c46' : '#4c211c';

  switch (unit.id) {
    case 'blue-garen':
      return (
        <svg viewBox="0 0 140 140" aria-hidden="true">
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#1f3f68" />
              <stop offset="100%" stopColor={unit.accent} />
            </linearGradient>
          </defs>
          <rect x="8" y="8" width="124" height="124" rx="28" fill={`url(#${gradientId})`} />
          <path d="M70 24 L88 58 L52 58 Z" fill="#f2d496" />
          <circle cx="70" cy="56" r="18" fill="#f2c9a6" />
          <path d="M50 48 Q70 18 90 48 L86 58 Q70 46 54 58 Z" fill="#355d95" />
          <path d="M38 118 L52 76 L88 76 L102 118 Z" fill="#244c70" />
          <rect x="60" y="72" width="20" height="38" rx="10" fill="#e0b764" />
          <path d="M102 28 L108 28 L108 90 L102 90 Z" fill="#d7d9df" />
          <path d="M96 22 L114 22 L105 8 Z" fill="#f4efe1" />
          <path d="M98 90 L112 90 L105 114 Z" fill="#8aa8d8" />
        </svg>
      );
    case 'blue-ahri':
      return (
        <svg viewBox="0 0 140 140" aria-hidden="true">
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#7f3850" />
              <stop offset="100%" stopColor={unit.accent} />
            </linearGradient>
          </defs>
          <rect x="8" y="8" width="124" height="124" rx="28" fill={`url(#${gradientId})`} />
          <path d="M42 38 L58 14 L66 42 Z" fill="#f6d7da" />
          <path d="M98 38 L82 14 L74 42 Z" fill="#f6d7da" />
          <circle cx="70" cy="58" r="18" fill="#f3cbb8" />
          <path d="M46 48 Q70 18 94 48 L88 74 Q70 58 52 74 Z" fill="#f2a3ab" />
          <path d="M34 118 Q50 78 64 110" fill="none" stroke="#ffe5ea" strokeWidth="10" strokeLinecap="round" />
          <path d="M54 122 Q70 80 84 112" fill="none" stroke="#ffe5ea" strokeWidth="10" strokeLinecap="round" />
          <path d="M76 118 Q92 78 108 110" fill="none" stroke="#ffe5ea" strokeWidth="10" strokeLinecap="round" />
          <circle cx="102" cy="92" r="10" fill="#8ee5ff" />
          <circle cx="102" cy="92" r="16" fill="#8ee5ff" opacity="0.24" />
        </svg>
      );
    case 'blue-jinx':
      return (
        <svg viewBox="0 0 140 140" aria-hidden="true">
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#173648" />
              <stop offset="100%" stopColor={unit.accent} />
            </linearGradient>
          </defs>
          <rect x="8" y="8" width="124" height="124" rx="28" fill={`url(#${gradientId})`} />
          <circle cx="70" cy="52" r="17" fill="#f1c6aa" />
          <path d="M44 44 Q70 18 96 44 L90 58 Q70 46 50 58 Z" fill="#6de5ef" />
          <path d="M48 60 Q42 92 28 118" fill="none" stroke="#49c7e6" strokeWidth="9" strokeLinecap="round" />
          <path d="M92 60 Q98 92 112 118" fill="none" stroke="#49c7e6" strokeWidth="9" strokeLinecap="round" />
          <path d="M48 112 L98 96 L106 112 L58 126 Z" fill="#303b5f" />
          <circle cx="94" cy="104" r="7" fill="#f26f80" />
          <path d="M36 104 L48 92" stroke="#f9db6a" strokeWidth="5" strokeLinecap="round" />
          <path d="M40 118 L54 104" stroke="#f9db6a" strokeWidth="5" strokeLinecap="round" />
        </svg>
      );
    case 'red-darius':
      return (
        <svg viewBox="0 0 140 140" aria-hidden="true">
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#511d18" />
              <stop offset="100%" stopColor={unit.accent} />
            </linearGradient>
          </defs>
          <rect x="8" y="8" width="124" height="124" rx="28" fill={`url(#${gradientId})`} />
          <circle cx="68" cy="54" r="18" fill="#efc2a1" />
          <path d="M46 44 Q68 18 92 42 L86 60 Q68 48 50 60 Z" fill="#271613" />
          <path d="M36 118 L50 76 L90 76 L104 118 Z" fill="#6b2a22" />
          <path d="M56 76 L46 102 L34 96 L44 70 Z" fill="#a83f31" />
          <path d="M110 26 L116 26 L116 92 L110 92 Z" fill="#d8dadf" />
          <path d="M92 22 L128 22 L114 44 Z" fill="#c54638" />
          <path d="M96 90 L128 90 L114 116 Z" fill="#d8dadf" />
        </svg>
      );
    case 'red-annie':
      return (
        <svg viewBox="0 0 140 140" aria-hidden="true">
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#59231b" />
              <stop offset="100%" stopColor={unit.accent} />
            </linearGradient>
          </defs>
          <rect x="8" y="8" width="124" height="124" rx="28" fill={`url(#${gradientId})`} />
          <circle cx="70" cy="56" r="18" fill="#efc3a3" />
          <circle cx="48" cy="40" r="11" fill="#5b2d26" />
          <circle cx="92" cy="40" r="11" fill="#5b2d26" />
          <path d="M48 48 Q70 22 92 48 L86 72 Q70 60 54 72 Z" fill="#6a382d" />
          <circle cx="98" cy="92" r="11" fill="#ff9e47" />
          <circle cx="98" cy="92" r="19" fill="#ff9e47" opacity="0.24" />
          <circle cx="44" cy="100" r="9" fill="#a46e43" />
          <circle cx="36" cy="92" r="5" fill="#a46e43" />
          <circle cx="52" cy="92" r="5" fill="#a46e43" />
          <rect x="36" y="102" width="16" height="18" rx="8" fill="#81522f" />
        </svg>
      );
    case 'red-caitlyn':
      return (
        <svg viewBox="0 0 140 140" aria-hidden="true">
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#28344b" />
              <stop offset="100%" stopColor={unit.accent} />
            </linearGradient>
          </defs>
          <rect x="8" y="8" width="124" height="124" rx="28" fill={`url(#${gradientId})`} />
          <circle cx="70" cy="56" r="18" fill="#efc9ad" />
          <rect x="46" y="24" width="48" height="14" rx="6" fill="#314769" />
          <rect x="54" y="12" width="30" height="22" rx="8" fill="#314769" />
          <path d="M48 44 Q70 24 92 44 L86 72 Q70 58 54 72 Z" fill="#536f9b" />
          <path d="M34 104 L108 92 L112 102 L38 114 Z" fill="#2e3343" />
          <circle cx="92" cy="98" r="8" fill="#c9cbd0" />
          <path d="M108 96 L124 94" stroke="#d8dbe4" strokeWidth="6" strokeLinecap="round" />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 140 140" aria-hidden="true">
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={shadowColor} />
              <stop offset="100%" stopColor={unit.accent} />
            </linearGradient>
          </defs>
          <rect x="8" y="8" width="124" height="124" rx="28" fill={`url(#${gradientId})`} />
          <circle cx="70" cy="56" r="20" fill="#f0d0b3" />
          <path d="M42 48 Q70 18 98 48 L90 72 Q70 60 50 72 Z" fill="#f4efe1" opacity="0.6" />
          <path d="M40 118 L54 78 L86 78 L100 118 Z" fill="#223447" />
        </svg>
      );
  }
}

export default function ChampionAvatar({
  unit,
  size = 'card',
}: {
  unit: AvatarUnit;
  size?: AvatarSize;
}) {
  const style = {
    '--avatar-accent': unit.accent,
    '--avatar-shadow': unit.team === 'blue' ? '#19343f' : '#49211b',
  } as CSSProperties;

  return (
    <div
      className={['champion-avatar', `avatar-${size}`, `team-${unit.team}`]
        .filter(Boolean)
        .join(' ')}
      style={style}
    >
      <AvatarIllustration unit={unit} />
    </div>
  );
}

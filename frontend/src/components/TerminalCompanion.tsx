import { useId } from 'react';
import portrait from '../assets/terminal-reference.jpg';

/** The supplied image is displayed through an SVG viewport, without altering its pixels. */
export function TerminalCompanion() {
  const id = useId().replace(/:/g, '');
  return (
    <div className="terminal-companion" aria-hidden="true">
      <svg className="companion-portrait" viewBox="378 100 330 458" focusable="false">
        <defs>
          <clipPath id={`${id}-eyes`}>
            <rect x="454" y="318" width="40" height="23" />
            <rect x="562" y="315" width="42" height="23" />
          </clipPath>
        </defs>
        <image href={portrait} width="736" height="736" />
        <g clipPath={`url(#${id}-eyes)`}>
          <rect x="450" y="310" width="160" height="34" fill="#000" />
          <image className="companion-eyes" href={portrait} width="736" height="736" />
        </g>
      </svg>
      <div className="companion-caption">
        <span>Default (ASI)</span>
        <strong>
          LOCAL
          <br />
          COMPANION
        </strong>
        <span>
          ESTUDAR.
          <br />
          ENTENDER.
          <br />
          CONSTRUIR.
        </span>
        <span className="companion-bars">▌▌▌ ▌ ▌▌▌▌</span>
      </div>
    </div>
  );
}

const base = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round",
};

export function IconTag(props) {
  return (
    <svg {...base} {...props}>
      <path d="M20.59 13.41 12 22 2 12V2h10l10 10v1.41Z" />
      <circle cx="7" cy="7" r="1.4" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function IconSearch(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  );
}

export function IconClose(props) {
  return (
    <svg {...base} {...props}>
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  );
}

export function IconFlame(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 2c1 3-2.5 4.5-2.5 8a3.5 3.5 0 0 0 7 0c0-1-.4-1.8-1-2.5.6 2-1 3.5-2.5 2-1-1 .3-2 0-4-.2-1.3-1-2.8-1-3.5Z" />
      <path d="M8.5 13.5A5 5 0 0 0 12 22a5 5 0 0 0 3.5-8.5" />
    </svg>
  );
}

export function IconTrendingUp(props) {
  return (
    <svg {...base} {...props}>
      <path d="m3 17 6-6 4 4 8-8" />
      <path d="M17 7h4v4" />
    </svg>
  );
}

export function IconGamepad(props) {
  return (
    <svg {...base} {...props}>
      <path d="M6 12h4M8 10v4" />
      <circle cx="17" cy="11" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="15" cy="13" r="0.8" fill="currentColor" stroke="none" />
      <path d="M6.5 7h11a4.5 4.5 0 0 1 4.46 5.14l-.62 4.32a2.5 2.5 0 0 1-4.42 1.2L15.5 16h-7l-1.42 1.66a2.5 2.5 0 0 1-4.42-1.2l-.62-4.32A4.5 4.5 0 0 1 6.5 7Z" />
    </svg>
  );
}

export function IconChevronDown(props) {
  return (
    <svg {...base} {...props}>
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

export function IconChevronUp(props) {
  return (
    <svg {...base} {...props}>
      <path d="m6 15 6-6 6 6" />
    </svg>
  );
}

export function IconGitHub(props) {
  return (
    <svg {...base} fill="currentColor" stroke="none" {...props}>
      <path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.89 1.52 2.34 1.08 2.91.83.09-.65.35-1.08.63-1.33-2.22-.25-4.56-1.11-4.56-4.95 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02a9.6 9.6 0 0 1 5 0c1.91-1.3 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.85-2.34 4.7-4.57 4.94.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2Z" />
    </svg>
  );
}

export function IconPlus(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

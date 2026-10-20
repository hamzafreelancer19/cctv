type IconProps = { className?: string };

const paths: Record<string, string> = {
  overview: "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z",
  camera: "M4 7h3l2-2h6l2 2h3v12H4V7zm8 3a3.5 3.5 0 100 7 3.5 3.5 0 000-7z",
  event: "M4 4h16v4H4V4zm0 6h16v10H4V10zm3 3v2h6v-2H7z",
  alert: "M12 2L1 21h22L12 2zm0 6l6.5 11h-13L12 8zm-1 4v3h2v-3h-2zm0 4v2h2v-2h-2z",
  people: "M8 11a3 3 0 100-6 3 3 0 000 6zm8 0a3 3 0 100-6 3 3 0 000 6zM2 19v-1c0-2.2 3-3.5 6-3.5s6 1.3 6 3.5v1H2zm14 0v-1c0-1.3-.5-2.3-1.3-3 2.5.2 5.3 1.4 5.3 3.5v.5h-4z",
  attendance: "M7 2v2H5a2 2 0 00-2 2v13a2 2 0 002 2h14a2 2 0 002-2V6a2 2 0 00-2-2h-2V2h-2v2H9V2H7zM5 9h14v10H5V9zm5.5 2.5l-3 3L6 13l-1 1 2.5 2.5L11.9 12l-1.4-1.4z",
  visitor: "M12 12a4 4 0 100-8 4 4 0 000 8zm-8 8a8 8 0 0116 0H4z",
  unknown: "M12 2a10 10 0 100 20 10 10 0 000-20zm1 15h-2v-2h2v2zm1.1-5.3l-.9.9c-.5.5-.7.9-.7 1.9h-2v-.5c0-.9.4-1.6.9-2.1l1.2-1.2c.3-.3.5-.7.5-1.1a1.9 1.9 0 00-3.8 0H8.4a4 4 0 118 0c0 .8-.3 1.5-.8 2z",
  zone: "M12 2l9 5v10l-9 5-9-5V7l9-5zm0 2.3L5 8v8l7 3.7L19 16V8l-7-3.7z",
  crowd: "M12 12a3 3 0 100-6 3 3 0 000 6zm-7 8a7 7 0 0114 0H5zm-3-3a5 5 0 013-4.6A4 4 0 001 17h1zm20 0h1a4 4 0 00-4-4.6 5 5 0 013 4.6z",
  object: "M3 3h8v8H3V3zm10 0h8v8h-8V3zM3 13h8v8H3v-8zm14 1h2v3h3v2h-3v3h-2v-3h-3v-2h3v-3z",
  risk: "M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2V9h2v5z",
  fire: "M12 2c1 3-1 4-2 6-1 2 0 4 2 4s2-3 1-5c3 2 4 5 4 7a7 7 0 11-14 0c0-3 2-6 5-8-1 3 1 4 2 4 .5-3-1-5-1-8z",
  smoke: "M6 19a3 3 0 010-6h.5A4 4 0 0114 9a4 4 0 014 4 3 3 0 010 6H6zm2 2h10v2H8v-2z",
  weapon: "M2 12h13l3-3 4 1-1 4-3-1-2 2H2v-3zm2 1v1h9l1-1H4z",
  fall: "M12 4a2 2 0 100-4 2 2 0 000 4zM4 22l4-8 3 2v6h2v-7l-3-2 1-4 3 3h4v-2h-3l-4-4-4 2-3 6 1 1 2-4 2 1-3 8h-2z",
  ppe: "M12 1L4 5v6c0 5 3.4 9 8 11 4.6-2 8-6 8-11V5l-8-4zm-1 14l-3-3 1.4-1.4L11 12.2l4.6-4.6L17 9l-6 6z",
  emergency: "M11 2h2v6h-2V2zm7.4 2.2l1.4 1.4-4.2 4.2-1.4-1.4 4.2-4.2zM2 11h6v2H2v-2zm14 0h6v2h-6v-2zM4.2 4.2L8.4 8.4 7 9.8 2.8 5.6l1.4-1.4zM11 16h2v6h-2v-6z",
  bell: "M12 2a6 6 0 00-6 6v4l-2 3v1h16v-1l-2-3V8a6 6 0 00-6-6zm0 20a3 3 0 003-3H9a3 3 0 003 3z",
  recording: "M12 4a8 8 0 100 16 8 8 0 000-16zm0 4a4 4 0 110 8 4 4 0 010-8z",
  evidence: "M4 4h10l6 6v10H4V4zm9 1.5V10h4.5L13 5.5zM8 13h8v2H8v-2zm0 4h8v2H8v-2z",
  system: "M4 4h16v12H4V4zm0 14h16v2H4v-2zM7 7v6h2V7H7zm4 2v4h2V9h-2zm4-1v5h2V8h-2z",
  logout: "M16 13v-2H7V8l-5 4 5 4v-3h9zM20 3h-9v2h9v14h-9v2h9a2 2 0 002-2V5a2 2 0 00-2-2z",
  trash: "M9 3h6l1 2h4v2H4V5h4l1-2zM6 9h12l-1 12H7L6 9zm4 2v8h1v-8h-1zm3 0v8h1v-8h-1z",
  vision: "M12 5c5 0 9.3 3.1 11 7-1.7 3.9-6 7-11 7S2.7 15.9 1 12c1.7-3.9 6-7 11-7zm0 2a5 5 0 100 10 5 5 0 000-10zm0 2.5a2.5 2.5 0 110 5 2.5 2.5 0 010-5z",
  menu: "M3 6h18v2H3V6zm0 5h18v2H3v-2zm0 5h18v2H3v-2z",
  close: "M6.4 4.6L12 10.2l5.6-5.6L19.4 6 13.8 11.6l5.6 5.6-1.4 1.4-5.6-5.6-5.6 5.6L5 17.2l5.6-5.6L5 6.1l1.4-1.5z",
  panel: "M4 4h16a2 2 0 012 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6a2 2 0 012-2zm0 2v12h4V6H4zm6 0v12h10V6H10z",
};

export default function Icon({ name, className }: IconProps & { name: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d={paths[name] || paths.overview} />
    </svg>
  );
}

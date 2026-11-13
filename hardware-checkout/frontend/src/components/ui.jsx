import { useState } from "react";
import { AlertIcon, CheckIcon, CopyIcon } from "./Icons.jsx";

export function Message({ msg }) {
  if (!msg?.text) return null;
  const isError = msg.type === "error";
  return (
    <div className={`alert ${msg.type}`} role={isError ? "alert" : "status"}>
      {isError ? <AlertIcon size={16} /> : <CheckIcon size={16} />}
      <span>{msg.text}</span>
    </div>
  );
}

export function Avatar({ name, size = 32 }) {
  let hue = 0;
  for (const c of name) hue = (hue * 31 + c.charCodeAt(0)) % 360;
  return (
    <span className="avatar" style={{ width: size, height: size, fontSize: size * 0.42, "--h": hue }} aria-hidden="true">
      {name.slice(0, 1).toUpperCase()}
    </span>
  );
}

export function RoleBadge({ owner }) {
  return <span className={`badge ${owner ? "owner" : "member"}`}>{owner ? "Owner" : "Member"}</span>;
}

export function Meter({ value, max }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div
      className={`meter${pct < 20 ? " low" : ""}`}
      role="meter"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={max}
    >
      <span style={{ width: `${pct}%` }} />
    </div>
  );
}

export function Skeleton({ w = "100%", h = 14 }) {
  return <span className="skeleton" style={{ width: w, height: h }} />;
}

export function SkeletonRows({ count = 3 }) {
  return (
    <div>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="row">
          <Skeleton w={36} h={36} />
          <div className="row-main skeleton-stack">
            <Skeleton w="40%" />
            <Skeleton w="65%" h={12} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function Empty({ icon, title, text, action }) {
  return (
    <div className="empty">
      <div className="empty-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{text}</p>
      {action}
    </div>
  );
}

export function CopyChip({ value }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable; ignore */
    }
  }

  return (
    <button type="button" className="id-chip copy" onClick={copy} title="Copy ProjectID">
      <code>{value}</code>
      {copied ? <CheckIcon size={13} /> : <CopyIcon size={13} />}
    </button>
  );
}

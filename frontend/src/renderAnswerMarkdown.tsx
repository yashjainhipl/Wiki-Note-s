import React from "react";

export function renderAnswerMarkdown(answer: string): React.ReactNode {
  const lines = answer.split("\n");
  const blocks: React.ReactNode[] = [];
  let bullets: string[] = [];

  const flushBullets = (key: string) => {
    if (!bullets.length) return;
    blocks.push(
      <ul className="query-bar__md-ul" key={`ul-${key}`}>
        {bullets.map((b, idx) => (
          <li className="query-bar__md-li" key={`li-${key}-${idx}`}>
            {inlineFormat(b)}
          </li>
        ))}
      </ul>,
    );
    bullets = [];
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushBullets(String(idx));
      return;
    }
    if (trimmed.startsWith("- ")) {
      bullets.push(trimmed.slice(2));
      return;
    }
    flushBullets(String(idx));
    blocks.push(
      <p className="query-bar__md-p" key={`p-${idx}`}>
        {inlineFormat(trimmed)}
      </p>,
    );
  });
  flushBullets("end");
  return <>{blocks}</>;
}

function inlineFormat(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={`s-${idx}`}>{part.slice(2, -2)}</strong>;
    }
    return <React.Fragment key={`t-${idx}`}>{part}</React.Fragment>;
  });
}

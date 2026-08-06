'use client';

import { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { Icons } from '../ui/Icons';
import { cn } from '../../utils/cn';

interface CodeBlockProps {
  language: string;
  value: string;
}

export function CodeBlock({ language, value }: CodeBlockProps) {
  const [isCopied, setIsCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(value);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div className="relative my-4 overflow-hidden rounded-xl bg-[#1E1E1E] border border-zinc-200 dark:border-zinc-800 shadow-xl group not-prose">
      {/* Header bar (Mac style) */}
      <div className="flex items-center justify-between px-4 py-2 bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
            <div className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
          </div>
          <span className="ml-2 text-xs font-mono text-zinc-400 uppercase tracking-wider">
            {language || 'text'}
          </span>
        </div>
        
        <button
          onClick={copyToClipboard}
          className="flex items-center gap-1.5 text-xs font-medium text-zinc-400 hover:text-white transition-colors p-1"
        >
          {isCopied ? (
            <>
              <Icons.Check className="w-3.5 h-3.5 text-green-400" />
              <span className="text-green-400">Copied</span>
            </>
          ) : (
            <>
              <Icons.Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code Content */}
      <div className="relative overflow-x-auto text-[13px] leading-relaxed">
        <SyntaxHighlighter
          language={language || 'text'}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            padding: '1rem',
            background: 'transparent',
          }}
          codeTagProps={{
            className: 'font-mono !bg-transparent !p-0 !text-inherit',
          }}
        >
          {value}
        </SyntaxHighlighter>
      </div>
    </div>
  );
}

/**
 * Reusable Evidence Type Icon Component
 * Pure presentational component
 */

import { FileText, Image, Mic, Video, File } from 'lucide-react';

interface EvidenceTypeIconProps {
  type: string;
}

export function EvidenceTypeIcon({ type }: EvidenceTypeIconProps) {
  const iconConfig: Record<string, { icon: React.ReactNode; className: string }> = {
    text: {
      icon: <FileText className="w-5 h-5" />,
      className: 'text-gray-500',
    },
    image: {
      icon: <Image className="w-5 h-5" />,
      className: 'text-blue-500',
    },
    audio: {
      icon: <Mic className="w-5 h-5" />,
      className: 'text-purple-500',
    },
    video: {
      icon: <Video className="w-5 h-5" />,
      className: 'text-red-500',
    },
    pdf: {
      icon: <File className="w-5 h-5" />,
      className: 'text-red-600',
    },
  };

  const config = iconConfig[type] || {
    icon: <File className="w-5 h-5" />,
    className: 'text-gray-400',
  };

  return <div className={config.className}>{config.icon}</div>;
}

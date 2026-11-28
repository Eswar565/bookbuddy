import React from 'react';
import type { IconWeight } from '@phosphor-icons/react';

// Individual tree-shaken imports
import { UserCircle } from '@phosphor-icons/react/dist/csr/UserCircle';
import { CaretDown } from '@phosphor-icons/react/dist/csr/CaretDown';
import { CaretLeft } from '@phosphor-icons/react/dist/csr/CaretLeft';
import { CaretRight } from '@phosphor-icons/react/dist/csr/CaretRight';
import { List } from '@phosphor-icons/react/dist/csr/List';
import { X } from '@phosphor-icons/react/dist/csr/X';
import { MagnifyingGlass } from '@phosphor-icons/react/dist/csr/MagnifyingGlass';
import { Sparkle } from '@phosphor-icons/react/dist/csr/Sparkle';
import { ArrowsDownUp } from '@phosphor-icons/react/dist/csr/ArrowsDownUp';
import { SquaresFour } from '@phosphor-icons/react/dist/csr/SquaresFour';
import { Funnel } from '@phosphor-icons/react/dist/csr/Funnel';
import { Globe } from '@phosphor-icons/react/dist/csr/Globe';
import { Heart } from '@phosphor-icons/react/dist/csr/Heart';
import { ShoppingBag } from '@phosphor-icons/react/dist/csr/ShoppingBag';
import { DownloadSimple } from '@phosphor-icons/react/dist/csr/DownloadSimple';
import { CheckCircle } from '@phosphor-icons/react/dist/csr/CheckCircle';
import { Prohibit } from '@phosphor-icons/react/dist/csr/Prohibit';
import { Plus } from '@phosphor-icons/react/dist/csr/Plus';
import { Check } from '@phosphor-icons/react/dist/csr/Check';
import { Trash } from '@phosphor-icons/react/dist/csr/Trash';
import { Storefront } from '@phosphor-icons/react/dist/csr/Storefront';
import { Truck } from '@phosphor-icons/react/dist/csr/Truck';
import { CalendarCheck } from '@phosphor-icons/react/dist/csr/CalendarCheck';
import { CalendarBlank } from '@phosphor-icons/react/dist/csr/CalendarBlank';
import { MapPin } from '@phosphor-icons/react/dist/csr/MapPin';
import { SealCheck } from '@phosphor-icons/react/dist/csr/SealCheck';
import { UsersThree } from '@phosphor-icons/react/dist/csr/UsersThree';
import { Newspaper } from '@phosphor-icons/react/dist/csr/Newspaper';
import { BookOpenText } from '@phosphor-icons/react/dist/csr/BookOpenText';
import { BookOpen } from '@phosphor-icons/react/dist/csr/BookOpen';
import { MicrophoneStage } from '@phosphor-icons/react/dist/csr/MicrophoneStage';
import { Trophy } from '@phosphor-icons/react/dist/csr/Trophy';
import { ChatsCircle } from '@phosphor-icons/react/dist/csr/ChatsCircle';
import { Image } from '@phosphor-icons/react/dist/csr/Image';
import { Handshake } from '@phosphor-icons/react/dist/csr/Handshake';
import { Headphones } from '@phosphor-icons/react/dist/csr/Headphones';
import { ArrowRight } from '@phosphor-icons/react/dist/csr/ArrowRight';
import { ArrowLeft } from '@phosphor-icons/react/dist/csr/ArrowLeft';
import { ArrowSquareOut } from '@phosphor-icons/react/dist/csr/ArrowSquareOut';
import { Phone } from '@phosphor-icons/react/dist/csr/Phone';
import { WhatsappLogo } from '@phosphor-icons/react/dist/csr/WhatsappLogo';
import { EnvelopeSimple } from '@phosphor-icons/react/dist/csr/EnvelopeSimple';
import { InstagramLogo } from '@phosphor-icons/react/dist/csr/InstagramLogo';
import { FacebookLogo } from '@phosphor-icons/react/dist/csr/FacebookLogo';
import { YoutubeLogo } from '@phosphor-icons/react/dist/csr/YoutubeLogo';
import { ArrowUp } from '@phosphor-icons/react/dist/csr/ArrowUp';
import { Warning } from '@phosphor-icons/react/dist/csr/Warning';
import { Info } from '@phosphor-icons/react/dist/csr/Info';
import { XCircle } from '@phosphor-icons/react/dist/csr/XCircle';
import { Clock } from '@phosphor-icons/react/dist/csr/Clock';
import { Eye } from '@phosphor-icons/react/dist/csr/Eye';
import { SignIn } from '@phosphor-icons/react/dist/csr/SignIn';
import { SignOut } from '@phosphor-icons/react/dist/csr/SignOut';
import { UserPlus } from '@phosphor-icons/react/dist/csr/UserPlus';
import { PaperPlaneTilt } from '@phosphor-icons/react/dist/csr/PaperPlaneTilt';

const ICON_MAP = {
  // Nav / header
  'user-circle': UserCircle,
  'caret-down': CaretDown,
  'caret-left': CaretLeft,
  'caret-right': CaretRight,
  'list': List,
  'x': X,

  // Catalogue
  'magnifying-glass': MagnifyingGlass,
  'sparkle': Sparkle,
  'arrows-down-up': ArrowsDownUp,
  'squares-four': SquaresFour,
  'funnel': Funnel,
  'globe': Globe,
  'heart': Heart,
  'heart-fill': Heart,
  'shopping-bag': ShoppingBag,
  'download-simple': DownloadSimple,
  'check-circle': CheckCircle,
  'prohibit': Prohibit,
  'plus': Plus,
  'check': Check,
  'trash': Trash,

  // Membership / delivery
  'storefront': Storefront,
  'truck': Truck,
  'calendar-check': CalendarCheck,
  'map-pin': MapPin,
  'seal-check': SealCheck,

  // Community / media
  'users-three': UsersThree,
  'newspaper': Newspaper,
  'book-open-text': BookOpenText,
  'book-open': BookOpen,
  'microphone-stage': MicrophoneStage,
  'calendar-blank': CalendarBlank,
  'trophy': Trophy,
  'chats-circle': ChatsCircle,
  'image': Image,
  'handshake': Handshake,
  'headphones': Headphones,
  'arrow-right': ArrowRight,
  'arrow-left': ArrowLeft,
  'arrow-square-out': ArrowSquareOut,
  'pen-nib': PaperPlaneTilt, // fallback / mapping

  // Contact / footer
  'phone': Phone,
  'whatsapp-logo': WhatsappLogo,
  'envelope-simple': EnvelopeSimple,
  'instagram-logo': InstagramLogo,
  'facebook-logo': FacebookLogo,
  'youtube-logo': YoutubeLogo,
  'arrow-up': ArrowUp,
  'paper-plane-tilt': PaperPlaneTilt,

  // Status / toasts
  'warning': Warning,
  'info': Info,
  'x-circle': XCircle,
  'clock': Clock,
  'eye': Eye,
  'sign-in': SignIn,
  'sign-out': SignOut,
  'user-plus': UserPlus,
} as const;

export type IconName = keyof typeof ICON_MAP;

export interface IconProps extends React.SVGAttributes<SVGSVGElement> {
  name: IconName;
  size?: number | string;
  weight?: IconWeight;
  color?: string;
  className?: string;
  style?: React.CSSProperties;
  'aria-hidden'?: boolean | 'true' | 'false';
  'aria-label'?: string;
}

export const Icon: React.FC<IconProps> = ({
  name,
  size = 20,
  weight,
  color = 'currentColor',
  className,
  style,
  'aria-hidden': ariaHidden = true,
  'aria-label': ariaLabel,
  ...rest
}) => {
  const Component = ICON_MAP[name];

  if (!Component) {
    if (process.env.NODE_ENV !== 'production') {
      console.warn(`[Icon] Unknown icon name: "${name}"`);
    }
    return null;
  }

  // Automatic fill weight for heart-fill
  const finalWeight = weight ?? (name === 'heart-fill' ? 'fill' : 'regular');

  return (
    <Component
      size={size}
      weight={finalWeight}
      color={color}
      className={className}
      style={{ verticalAlign: 'middle', flexShrink: 0, ...style }}
      aria-hidden={ariaLabel ? false : ariaHidden}
      aria-label={ariaLabel}
      {...rest}
    />
  );
};

export default Icon;

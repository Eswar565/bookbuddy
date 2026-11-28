import React from 'react';
import ReactDOMServer from 'react-dom/server';
import fs from 'fs';
import path from 'path';

// Import all icons from CSR bundle
import * as Phosphor from '@phosphor-icons/react';

const iconsToGenerate = [
  // Nav/header
  { name: 'user-circle', comp: 'UserCircle' },
  { name: 'caret-down', comp: 'CaretDown' },
  { name: 'caret-left', comp: 'CaretLeft' },
  { name: 'caret-right', comp: 'CaretRight' },
  { name: 'caret-up', comp: 'CaretUp' },
  { name: 'list', comp: 'List' },
  { name: 'x', comp: 'X' },

  // Catalogue
  { name: 'magnifying-glass', comp: 'MagnifyingGlass' },
  { name: 'sparkle', comp: 'Sparkle' },
  { name: 'arrows-down-up', comp: 'ArrowsDownUp' },
  { name: 'squares-four', comp: 'SquaresFour' },
  { name: 'funnel', comp: 'Funnel' },
  { name: 'globe', comp: 'Globe' },
  { name: 'heart', comp: 'Heart' },
  { name: 'heart-fill', comp: 'Heart', weight: 'fill' },
  { name: 'shopping-bag', comp: 'ShoppingBag' },
  { name: 'download-simple', comp: 'DownloadSimple' },
  { name: 'check-circle', comp: 'CheckCircle' },
  { name: 'check-circle-fill', comp: 'CheckCircle', weight: 'fill' },
  { name: 'prohibit', comp: 'Prohibit' },
  { name: 'plus', comp: 'Plus' },
  { name: 'check', comp: 'Check' },
  { name: 'trash', comp: 'Trash' },

  // Membership/delivery
  { name: 'storefront', comp: 'Storefront' },
  { name: 'storefront-duotone', comp: 'Storefront', weight: 'duotone' },
  { name: 'truck', comp: 'Truck' },
  { name: 'truck-duotone', comp: 'Truck', weight: 'duotone' },
  { name: 'calendar-check', comp: 'CalendarCheck' },
  { name: 'map-pin', comp: 'MapPin' },
  { name: 'seal-check', comp: 'SealCheck' },
  { name: 'seal-check-fill', comp: 'SealCheck', weight: 'fill' },

  // Community/media
  { name: 'users-three', comp: 'UsersThree' },
  { name: 'users-three-duotone', comp: 'UsersThree', weight: 'duotone' },
  { name: 'newspaper', comp: 'Newspaper' },
  { name: 'newspaper-duotone', comp: 'Newspaper', weight: 'duotone' },
  { name: 'book-open-text', comp: 'BookOpenText' },
  { name: 'book-open-text-duotone', comp: 'BookOpenText', weight: 'duotone' },
  { name: 'microphone-stage', comp: 'MicrophoneStage' },
  { name: 'microphone-stage-duotone', comp: 'MicrophoneStage', weight: 'duotone' },
  { name: 'calendar-blank', comp: 'CalendarBlank' },
  { name: 'trophy', comp: 'Trophy' },
  { name: 'trophy-duotone', comp: 'Trophy', weight: 'duotone' },
  { name: 'chats-circle', comp: 'ChatsCircle' },
  { name: 'image', comp: 'Image' },
  { name: 'handshake', comp: 'Handshake' },
  { name: 'handshake-duotone', comp: 'Handshake', weight: 'duotone' },
  { name: 'book-open', comp: 'BookOpen' },
  { name: 'headphones', comp: 'Headphones' },
  { name: 'arrow-right', comp: 'ArrowRight' },
  { name: 'arrow-left', comp: 'ArrowLeft' },
  { name: 'arrow-square-out', comp: 'ArrowSquareOut' },

  // Contact/footer
  { name: 'phone', comp: 'Phone' },
  { name: 'whatsapp-logo', comp: 'WhatsappLogo' },
  { name: 'envelope-simple', comp: 'EnvelopeSimple' },
  { name: 'instagram-logo', comp: 'InstagramLogo' },
  { name: 'facebook-logo', comp: 'FacebookLogo' },
  { name: 'youtube-logo', comp: 'YoutubeLogo' },
  { name: 'arrow-up', comp: 'ArrowUp' },
  { name: 'paper-plane-tilt', comp: 'PaperPlaneTilt' },

  // Status/toasts & UI
  { name: 'warning', comp: 'Warning' },
  { name: 'info', comp: 'Info' },
  { name: 'x-circle', comp: 'XCircle' },
  { name: 'clock', comp: 'Clock' },
  { name: 'eye', comp: 'Eye' },
  { name: 'sign-in', comp: 'SignIn' },
  { name: 'sign-out', comp: 'SignOut' },
  { name: 'user-plus', comp: 'UserPlus' },
  { name: 'sliders', comp: 'Sliders' },
  { name: 'shield', comp: 'Shield' },
  { name: 'star', comp: 'Star' },
  { name: 'star-fill', comp: 'Star', weight: 'fill' },
  { name: 'play', comp: 'Play' },
];

// Legacy alias mapping so existing <use href="#i-NAME" /> or #ph-NAME works smoothly
const legacyAliases = {
  'home': 'storefront',
  'library': 'book-open',
  'calendar': 'calendar-blank',
  'envelope': 'envelope-simple',
  'mail': 'envelope-simple',
  'users': 'users-three',
  'user-circle': 'user-circle',
  'chevron-down': 'caret-down',
  'chevron-up': 'caret-up',
  'chevron-left': 'caret-left',
  'chevron-right': 'caret-right',
  'arrow-right': 'arrow-right',
  'arrow-left': 'arrow-left',
  'bars': 'list',
  'search': 'magnifying-glass',
  'filter': 'funnel',
  'x': 'x',
  'plus': 'plus',
  'check': 'check',
  'check-circle': 'check-circle',
  'trash': 'trash',
  'whatsapp': 'whatsapp-logo',
  'download': 'download-simple',
  'map-pin': 'map-pin',
  'phone': 'phone',
  'eye': 'eye',
  'trophy': 'trophy',
  'image': 'image',
  'headphones': 'headphones',
  'id-card': 'user-circle',
  'sliders': 'sliders',
  'newspaper': 'newspaper',
  'star': 'star',
  'play': 'play',
  'sign-out': 'sign-out',
  'sign-in': 'sign-in',
  'user-plus': 'user-plus',
  'shield': 'shield',
  'external-link': 'arrow-square-out',
};

let symbols = [];

for (const item of iconsToGenerate) {
  const Component = Phosphor[item.comp];
  if (!Component) {
    console.warn('Missing component:', item.comp);
    continue;
  }
  const weight = item.weight || 'regular';
  const element = React.createElement(Component, { weight, size: 256, color: 'currentColor' });
  const html = ReactDOMServer.renderToStaticMarkup(element);
  
  // Extract the inner SVG elements
  const innerMatch = html.match(/<svg[^>]*>([\s\S]*?)<\/svg>/i);
  const innerContent = innerMatch ? innerMatch[1] : '';

  symbols.push(`  <symbol id="ph-${item.name}" viewBox="0 0 256 256">
    ${innerContent}
  </symbol>`);
}

// Add legacy alias symbols
for (const [legacyName, phName] of Object.entries(legacyAliases)) {
  const item = iconsToGenerate.find(i => i.name === phName);
  if (item) {
    const Component = Phosphor[item.comp];
    const weight = item.weight || 'regular';
    const element = React.createElement(Component, { weight, size: 256, color: 'currentColor' });
    const html = ReactDOMServer.renderToStaticMarkup(element);
    const innerMatch = html.match(/<svg[^>]*>([\s\S]*?)<\/svg>/i);
    const innerContent = innerMatch ? innerMatch[1] : '';

    symbols.push(`  <symbol id="i-${legacyName}" viewBox="0 0 256 256">
    ${innerContent}
  </symbol>`);
  }
}

const spriteSvg = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="display:none;" aria-hidden="true">
${symbols.join('\n')}
</svg>`;

// Write sprite.svg to backend/app/static/icons/sprite.svg and static/icons/sprite.svg
const backendIconsDir = path.resolve('..', 'backend', 'app', 'static', 'icons');
const rootIconsDir = path.resolve('..', 'static', 'icons');
fs.mkdirSync(backendIconsDir, { recursive: true });
fs.mkdirSync(rootIconsDir, { recursive: true });

fs.writeFileSync(path.join(backendIconsDir, 'sprite.svg'), spriteSvg, 'utf8');
fs.writeFileSync(path.join(rootIconsDir, 'sprite.svg'), spriteSvg, 'utf8');
console.log('Successfully generated sprite.svg at', path.join(backendIconsDir, 'sprite.svg'));

// Also update backend/app/templates/workspace/_icons.html with inline symbols
const iconsHtml = `<div style="display:none;" aria-hidden="true">
${spriteSvg}
</div>
`;
const iconsTemplatePath = path.resolve('..', 'backend', 'app', 'templates', 'workspace', '_icons.html');
fs.writeFileSync(iconsTemplatePath, iconsHtml, 'utf8');
console.log('Successfully updated', iconsTemplatePath);

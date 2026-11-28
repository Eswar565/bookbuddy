import React, { useState, useRef, useEffect, ReactNode } from 'react';
import './dropdown.css';

export interface DropdownItemProps {
  val: string;
  label: ReactNode;
  icon?: ReactNode;
  checked?: boolean;
}

export interface DropdownProps {
  id?: string;
  label: ReactNode;
  items: DropdownItemProps[];
  selectedValue?: string;
  onSelect: (val: string) => void;
  className?: string;
  ariaLabel?: string;
}

export const Dropdown: React.FC<DropdownProps> = ({
  id,
  label,
  items,
  selectedValue,
  onSelect,
  className = '',
  ariaLabel,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isUp, setIsUp] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Check positioning
  useEffect(() => {
    if (isOpen && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      const spaceBelow = window.innerHeight - rect.bottom;
      const spaceAbove = rect.top;
      if (spaceBelow < 280 && spaceAbove > spaceBelow) {
        setIsUp(true);
      } else {
        setIsUp(false);
      }
    }
  }, [isOpen]);

  // Click outside & Escape listener
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
        triggerRef.current?.focus();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  // Keyboard navigation within menu
  const handleMenuKeyDown = (e: React.KeyboardEvent) => {
    const menu = menuRef.current;
    if (!menu) return;
    const itemElements = Array.from(
      menu.querySelectorAll<HTMLButtonElement>('.dropdown-item:not([disabled])')
    );
    const currentIndex = itemElements.indexOf(document.activeElement as HTMLButtonElement);

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      const nextIndex = currentIndex < itemElements.length - 1 ? currentIndex + 1 : 0;
      itemElements[nextIndex]?.focus();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const prevIndex = currentIndex > 0 ? currentIndex - 1 : itemElements.length - 1;
      itemElements[prevIndex]?.focus();
    } else if (e.key === 'Home') {
      e.preventDefault();
      itemElements[0]?.focus();
    } else if (e.key === 'End') {
      e.preventDefault();
      itemElements[itemElements.length - 1]?.focus();
    }
  };

  return (
    <div
      ref={containerRef}
      className={`dropdown-container ${className}`}
      style={{ position: 'relative', width: '100%' }}
      onKeyDown={handleMenuKeyDown}
    >
      <button
        ref={triggerRef}
        id={id ? `${id}-btn` : undefined}
        type="button"
        className="dropdown-trigger"
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-label={ariaLabel}
        onClick={() => setIsOpen((prev) => !prev)}
      >
        <span>{label}</span>
        <svg
          className="bb-chevron"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {isOpen && (
        <div
          ref={menuRef}
          id={id ? `${id}-menu` : undefined}
          role="menu"
          className={`dropdown-menu ${isUp ? 'dropdown-menu--up' : ''}`}
        >
          {items.map((item) => {
            const isSelected = selectedValue !== undefined ? selectedValue === item.val : item.checked;
            return (
              <button
                key={item.val}
                type="button"
                role="menuitem"
                aria-selected={isSelected}
                className={`dropdown-item ${isSelected ? 'is-selected' : ''}`}
                onClick={() => {
                  onSelect(item.val);
                  setIsOpen(false);
                  triggerRef.current?.focus();
                }}
              >
                <span>{item.label}</span>
                <svg
                  className="check"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

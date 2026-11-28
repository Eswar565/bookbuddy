import React, { useState, useRef, useEffect } from 'react';
import './dropdown.css';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps {
  id?: string;
  name?: string;
  options: SelectOption[];
  value?: string;
  defaultValue?: string;
  onChange?: (val: string) => void;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  ariaLabel?: string;
}

export const Select: React.FC<SelectProps> = ({
  id,
  name,
  options,
  value: controlledValue,
  defaultValue,
  onChange,
  placeholder = 'Select an option',
  disabled = false,
  required = false,
  className = '',
  ariaLabel,
}) => {
  const [internalValue, setInternalValue] = useState<string>(
    controlledValue !== undefined ? controlledValue : (defaultValue || (options[0]?.value ?? ''))
  );
  const [isOpen, setIsOpen] = useState(false);
  const [isUp, setIsUp] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const hiddenSelectRef = useRef<HTMLSelectElement>(null);

  const currentValue = controlledValue !== undefined ? controlledValue : internalValue;
  const currentOption = options.find((opt) => opt.value === currentValue);
  const displayLabel = currentOption ? currentOption.label : placeholder;

  useEffect(() => {
    if (controlledValue !== undefined) {
      setInternalValue(controlledValue);
    }
  }, [controlledValue]);

  // Flip-up logic
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

  // Outside click & escape listener
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

  const handleSelect = (val: string) => {
    if (controlledValue === undefined) {
      setInternalValue(val);
    }
    if (hiddenSelectRef.current) {
      hiddenSelectRef.current.value = val;
      hiddenSelectRef.current.dispatchEvent(new Event('change', { bubbles: true }));
      hiddenSelectRef.current.dispatchEvent(new Event('input', { bubbles: true }));
    }
    onChange?.(val);
    setIsOpen(false);
    triggerRef.current?.focus();
  };

  // Keyboard navigation within listbox
  const handleMenuKeyDown = (e: React.KeyboardEvent) => {
    const menu = menuRef.current;
    if (!menu) return;
    const itemElements = Array.from(
      menu.querySelectorAll<HTMLButtonElement>('.bb-select-item:not([disabled])')
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
      className={`bb-custom-select-wrap ${className}`}
      style={{ position: 'relative', width: '100%' }}
      onKeyDown={handleMenuKeyDown}
    >
      {/* Hidden native select for full form/accessibility sync */}
      <select
        ref={hiddenSelectRef}
        id={id}
        name={name}
        value={currentValue}
        required={required}
        disabled={disabled}
        aria-hidden="true"
        tabIndex={-1}
        style={{
          position: 'absolute',
          opacity: 0,
          pointerEvents: 'none',
          width: '100%',
          height: '100%',
          top: 0,
          left: 0,
          zIndex: -1,
        }}
        onChange={(e) => handleSelect(e.target.value)}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value} disabled={opt.disabled}>
            {opt.label}
          </option>
        ))}
      </select>

      {/* Styled custom trigger */}
      <button
        ref={triggerRef}
        type="button"
        className="bb-select-trigger"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={ariaLabel}
        disabled={disabled}
        onClick={() => setIsOpen((prev) => !prev)}
      >
        <span className="bb-select-value">{displayLabel}</span>
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

      {/* Styled listbox menu */}
      {isOpen && (
        <div
          ref={menuRef}
          role="listbox"
          className={`bb-select-menu dropdown-menu ${isUp ? 'bb-select-menu--up' : ''}`}
        >
          {options.map((opt) => {
            const isSelected = opt.value === currentValue;
            return (
              <button
                key={opt.value}
                type="button"
                role="option"
                aria-selected={isSelected}
                disabled={opt.disabled}
                className={`bb-select-item dropdown-item ${isSelected ? 'is-selected' : ''}`}
                onClick={() => handleSelect(opt.value)}
              >
                <span>{opt.label}</span>
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

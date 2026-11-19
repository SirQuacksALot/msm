import type { GlobalThemeOverrides } from 'naive-ui'

function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

/**
 * Liest beim Aufruf die aktuellen Werte aus style.css @theme.
 * Wird in App.vue's setup() aufgerufen → DOM ist zu diesem Zeitpunkt bereit.
 */
export function getThemeOverrides(): GlobalThemeOverrides {
  return {
    common: {
      primaryColor:        cssVar('--color-accent'),
      primaryColorHover:   cssVar('--color-accent-hover'),
      primaryColorPressed: cssVar('--color-accent-pressed'),
      primaryColorSuppl:   cssVar('--color-accent'),
      bodyColor:           cssVar('--color-bg'),
      cardColor:           cssVar('--color-surface'),
      modalColor:          cssVar('--color-surface'),
      popoverColor:        cssVar('--color-elevated'),
      borderColor:         cssVar('--color-border'),
      dividerColor:        cssVar('--color-border'),
      textColorBase:       cssVar('--color-fg'),
      textColor1:          cssVar('--color-fg'),
      textColor2:          cssVar('--color-muted'),
      textColor3:          cssVar('--color-dim'),
      borderRadius: '8px',
      fontFamily: 'ui-sans-serif, system-ui, -apple-system, sans-serif',
    },
    Card: {
      color:           cssVar('--color-surface'),
      borderColor:     cssVar('--color-border'),
      titleFontWeight: '600',
      titleTextColor:  cssVar('--color-muted'),
    },
    Button: {
      borderRadiusMedium: '6px',
      borderRadiusSmall:  '5px',
      colorPrimary:        cssVar('--color-accent'),
      colorHoverPrimary:   cssVar('--color-accent-hover'),
      colorPressedPrimary: cssVar('--color-accent-pressed'),
      textColorPrimary:    '#ffffff',
    },
    Tag: { borderRadius: '999px' },
  }
}
/** Theme constants shared by the server layout (init script) and useTheme. */

export const THEME_STORAGE_KEY = "linen-theme";

/**
 * Runs in <head> before paint: applies the persisted theme (or the system
 * preference) to `data-theme` so there is no flash of the wrong theme.
 */
export const THEME_INIT_SCRIPT = `(()=>{try{var t=localStorage.getItem('${THEME_STORAGE_KEY}');if(t!=='light'&&t!=='dark'){t=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}document.documentElement.dataset.theme=t;}catch(e){document.documentElement.dataset.theme='light';}})();`;

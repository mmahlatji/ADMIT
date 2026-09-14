import { createTheme, rem, type MantineColorsTuple } from "@mantine/core";

// Institutional blue. Swap these for the official UCT brand values if the
// brand guide is to hand: shade 8 is what filled buttons use in light mode,
// shade 5 in dark, and the rest are derived hover/border/tint steps.
const uct: MantineColorsTuple = [
  "#eff5fa",
  "#dbe7f2",
  "#b5cde6",
  "#8bb1d9",
  "#6899cf",
  "#518ac9",
  "#4483c7",
  "#366fae",
  "#2c5f97",
  "#123f66",
];

// Warm counterweight to all that blue, used only where something needs a
// person to look at it: flagged rows, pending conflicts, unapproved accounts.
const attention: MantineColorsTuple = [
  "#fff8e6",
  "#ffefcc",
  "#ffdd99",
  "#ffca63",
  "#ffba36",
  "#ffb018",
  "#ffab06",
  "#e39500",
  "#ca8400",
  "#af7100",
];

export const theme = createTheme({
  colors: { uct, attention },
  primaryColor: "uct",
  // 8 on light keeps white button text at ~6.7:1, comfortably past AA
  primaryShade: { light: 8, dark: 5 },

  // Atkinson Hyperlegible is drawn so 1/l/I and 0/O stay distinguishable,
  // which matters on screens that are mostly campus ids and application
  // numbers. Crimson Pro carries the institutional register in headings.
  fontFamily: '"Atkinson Hyperlegible", system-ui, sans-serif',
  fontFamilyMonospace: '"Fira Mono", ui-monospace, monospace',
  headings: {
    fontFamily: '"Crimson Pro", Georgia, serif',
    fontWeight: "600",
    sizes: {
      h1: { fontSize: rem(30), lineHeight: "1.25" },
      h2: { fontSize: rem(24), lineHeight: "1.3" },
      h3: { fontSize: rem(19), lineHeight: "1.35" },
      h4: { fontSize: rem(17), lineHeight: "1.4" },
    },
  },

  defaultRadius: "sm",
  cursorType: "pointer",
  focusRing: "auto",

  components: {
    Table: {
      defaultProps: {
        highlightOnHover: true,
        verticalSpacing: "xs",
        horizontalSpacing: "md",
        stickyHeader: true,
      },
    },
    Card: { defaultProps: { withBorder: true, padding: "lg", radius: "sm" } },
    Paper: { defaultProps: { radius: "sm" } },
    Badge: { defaultProps: { radius: "sm", variant: "light" } },
    Button: { defaultProps: { radius: "sm" } },
    TextInput: { defaultProps: { radius: "sm" } },
    PasswordInput: { defaultProps: { radius: "sm" } },
    Select: { defaultProps: { radius: "sm", checkIconPosition: "right" } },
    Modal: { defaultProps: { radius: "sm", centered: true } },
    Tooltip: { defaultProps: { withArrow: true, openDelay: 300 } },
  },
});

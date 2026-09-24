import { Variants } from 'framer-motion';

// Page transition — FAST, no wait
export const pageVariants: Variants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.22, ease: [0.22, 1, 0.36, 1] } },
  exit: { opacity: 0, y: -4, transition: { duration: 0.12, ease: "easeIn" } },
};

// Stagger container for KPI cards — FAST, no perceived delay
export const staggerContainer: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.04, delayChildren: 0.02 } },
};

// Bouncy card entrance
export const bouncyCard: Variants = {
  hidden: { opacity: 0, y: 20, scale: 0.96 },
  visible: {
    opacity: 1, y: 0, scale: 1,
    transition: { type: "spring", stiffness: 380, damping: 22, mass: 0.7 },
  },
};

// While in view — scroll reveal
export const scrollReveal: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1, y: 0,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  },
};

// Button tap
export const tapBouncy = {
  whileHover: { scale: 1.02, transition: { type: "spring", stiffness: 400 } },
  whileTap: { scale: 0.97 },
};

// Nav hover
export const navHover = {
  whileHover: { y: -1 },
  whileTap: { y: 0 },
};

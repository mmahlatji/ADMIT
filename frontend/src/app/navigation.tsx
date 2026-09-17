import {
  ClipboardList,
  Download,
  FileSpreadsheet,
  Gavel,
  LayoutDashboard,
  Scale,
  ScrollText,
  TriangleAlert,
  Users,
} from "lucide-react";
import type { Role } from "../types/api";
import { CONVENOR_ADMIN, CONVENOR_ONLY, READ_ROLES } from "../lib/roles";

export type NavItem = {
  label: string;
  to: string;
  icon: React.ReactNode;
  roles: Role[];
  /** Rendered as a count next to the label when the shell has one to show. */
  badgeKey?: "conflicts" | "pendingUsers";
};

export type NavSection = { title: string; items: NavItem[] };

const size = 18;

export const navigation: NavSection[] = [
  {
    title: "Intake",
    items: [
      {
        label: "Overview",
        to: "/",
        icon: <LayoutDashboard size={size} />,
        roles: READ_ROLES,
      },
      {
        label: "Applicants",
        to: "/applicants",
        icon: <Users size={size} />,
        roles: READ_ROLES,
      },
      {
        label: "Decisions",
        to: "/decisions",
        icon: <Gavel size={size} />,
        roles: READ_ROLES,
      },
    ],
  },
  {
    title: "Data",
    items: [
      {
        label: "Imports",
        to: "/imports",
        icon: <FileSpreadsheet size={size} />,
        roles: CONVENOR_ADMIN,
      },
      {
        label: "Conflicts",
        to: "/conflicts",
        icon: <TriangleAlert size={size} />,
        roles: CONVENOR_ADMIN,
        badgeKey: "conflicts",
      },
      {
        label: "Admission rules",
        to: "/rules",
        icon: <Scale size={size} />,
        roles: READ_ROLES,
      },
      {
        label: "Exports",
        to: "/exports",
        icon: <Download size={size} />,
        roles: CONVENOR_ADMIN,
      },
    ],
  },
  {
    title: "Administration",
    items: [
      {
        label: "People",
        to: "/people",
        icon: <ClipboardList size={size} />,
        roles: CONVENOR_ONLY,
        badgeKey: "pendingUsers",
      },
      {
        label: "Audit log",
        to: "/audit",
        icon: <ScrollText size={size} />,
        roles: CONVENOR_ADMIN,
      },
    ],
  },
];

import { File, Scale, TriangleAlert, Users } from "lucide-react";
import { Role } from "../types/user";

// config/dashboardTiles.tsx
export type TileConfig = {
  title: string;
  icon: React.ReactNode;
  to: string;
  roles: Role[]; // who can see this tile
};

export const dashboardTiles: TileConfig[] = [
  {
    title: "Upload Documents",
    icon: <File size={40} />,
    to: "/file-upload",
    // POST /imports/{source_type} is convenor+admin. Committee used to be
    // listed here and admin was not, so committee saw a tile that 403s and
    // admin was hidden from something they are allowed to do.
    roles: ["convenor", "admin"],
  },
  {
    title: "Decisions",
    icon: <Scale size={40} />,
    to: "/decisions",
    roles: ["admin", "committee", "convenor"],
  },
  {
    title: "Resolve conflicts",
    icon: <TriangleAlert size={40} />,
    to: "/matching-reviews",
    // /matching_reviews is convenor+admin on the backend, not committee
    roles: ["convenor", "admin"],
  },
  {
    title: "Workspace",
    icon: <Users size={40} />,
    // was "/assign", the same path as the Assign roles tile below, so the two
    // tiles went to the same place. This page isn't built yet either, so the
    // catch-all route in App.tsx sends it back to the dashboard for now.
    to: "/workspace",
    roles: ["convenor", "admin", "committee"],
  },
  {
    title: "Assign roles",
    icon: <Users size={40} />,
    to: "/assign",
    roles: ["convenor"],
  },
  // ...
];

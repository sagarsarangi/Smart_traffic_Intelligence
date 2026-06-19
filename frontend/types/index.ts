// Shared Types and Interfaces

// ---------------------------------------------------------------------------
// Traffic dashboard types
// ---------------------------------------------------------------------------

/** A submitted incident pin shown on the city map heatmap. */
export interface IncidentPin {
    /** Latitude of the resolved location. */
    lat: number;
    /** Longitude of the resolved location. */
    lng: number;
    /** Display zone / area name (AI-resolved canonical name). */
    zone: string;
    /** Unique identifier so React can key the list. */
    id: string;
}


export interface SystemData {
  name: string;
  contact: {
    email: string;
    portfolio: string;
    links: SocialLink[];
  };
  summary: string;
  workExperience: WorkExperience[];
  education: Education[];
  projects: Project[];
  skills: Skills;
  achievements: Achievement[];
}

export interface SocialLink {
  name: string;
  url: string;
  icon: React.ComponentType<{ className?: string; weight?: "thin" | "light" | "regular" | "bold" | "fill" | "duotone"; size?: number | string }>;
}

export interface WorkExperience {
  title: string;
  company: string;
  place: string;
  date: string;
  description: string;
  points: string[];
}

export interface Education {
  degree: string;
  institution: string;
  date: string;
  details: string;
}

export interface Project {
  title: string;
  tech: string[];
  description: string;
  points: string[];
  url: string;
  image?: string;
}

export interface Skills {
  programming: string[];
  ai_ml: string[];
  data: string[];
  misc: string[];
  soft: string[];
}

export interface Achievement {
  title: string;
  organization: string;
  date: string;
  points: string[];
}

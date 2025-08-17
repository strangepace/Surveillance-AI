import { useEffect } from "react";

type SEOProps = {
  title: string;
  description?: string;
  canonical?: string;
};

export const SEOHead = ({ title, description, canonical }: SEOProps) => {
  useEffect(() => {
    document.title = title;

    if (description) {
      let meta = document.querySelector('meta[name="description"]');
      if (!meta) {
        meta = document.createElement("meta");
        meta.setAttribute("name", "description");
        document.head.appendChild(meta);
      }
      meta.setAttribute("content", description);
    }

    const linkRel = "canonical";
    let link = document.querySelector(`link[rel="${linkRel}"]`);
    if (!link) {
      link = document.createElement("link");
      link.setAttribute("rel", linkRel);
      document.head.appendChild(link);
    }
    const href = canonical || window.location.href;
    link.setAttribute("href", href);
  }, [title, description, canonical]);

  return null;
};

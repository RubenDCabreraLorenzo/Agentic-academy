/**
 * Document title and description. index.html keeps static values for clients that do not run scripts
 * (research R8, R15), so these are set directly rather than through a rendered title element.
 */
import { useEffect } from "react";
import { useTranslation } from "react-i18next";

export function usePageMeta({ title, description }: { title: string; description?: string | undefined }): void {
  const { t } = useTranslation();
  const product = t("app.name");

  useEffect(() => {
    document.title = `${title} · ${product}`;
  }, [title, product]);

  useEffect(() => {
    if (!description) return;
    let meta = document.head.querySelector<HTMLMetaElement>('meta[name="description"]');
    if (!meta) {
      meta = document.createElement("meta");
      meta.name = "description";
      document.head.appendChild(meta);
    }
    meta.content = description;
  }, [description]);
}

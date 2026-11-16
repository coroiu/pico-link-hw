# Local docker-compose preview service: auto-exports hardware/*.kicad_pcb and
# enclosure/*.scad into GLB models + 2D renders, serves them with a
# <model-viewer> page, and re-exports on file change (see ../bd show
# pilink-1n7 for the full design).
#
# Base image ships kicad-cli (pcb -> glb/svg export). We add OpenSCAD
# (scad -> stl), trimesh (stl -> glb, since OpenSCAD has no native glTF
# export), inotify-tools (file watcher) and curl (to vendor model-viewer at
# build time so the page works without internet access on the LAN).
FROM kicad/kicad:10.0

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openscad \
        inotify-tools \
        python3-pip \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir --break-system-packages trimesh

WORKDIR /preview

COPY scripts/ /preview/scripts/
COPY site/ /preview/site/
RUN chmod +x /preview/scripts/*.sh

# Vendor the model-viewer web component locally (pinned version) so the page
# renders for phones on the LAN even without internet access.
RUN mkdir -p /preview/site/vendor \
    && curl -fsSL \
        "https://unpkg.com/@google/model-viewer@3.5.0/dist/model-viewer.min.js" \
        -o /preview/site/vendor/model-viewer.min.js

ENV SITE_DIR=/preview/site \
    HARDWARE_DIR=/work/hardware \
    ENCLOSURE_DIR=/work/enclosure \
    PORT=8787

EXPOSE 8787

ENTRYPOINT ["/preview/scripts/entrypoint.sh"]

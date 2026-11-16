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
        nodejs \
        npm \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir --break-system-packages trimesh

# gltf-transform post-processes the kicad-cli PCB GLB (see export.sh): the raw
# export is ~17k separate primitives (one per track/pad/via/zone fragment),
# which is what makes the browser view laggy -- `optimize` joins them into
# 3 draw calls and meshopt-compresses the buffers. Pinned for reproducible
# builds.
RUN npm install -g --no-audit --no-fund @gltf-transform/cli@4.5.1 \
    && npm cache clean --force

WORKDIR /preview

COPY scripts/ /preview/scripts/
COPY site/ /preview/site/
RUN chmod +x /preview/scripts/*.sh

# Vendor the model-viewer web component locally (pinned version) so the page
# renders for phones on the LAN even without internet access.
RUN mkdir -p /preview/site/vendor \
    && curl -fsSL \
        "https://unpkg.com/@google/model-viewer@3.5.0/dist/model-viewer.min.js" \
        -o /preview/site/vendor/model-viewer.min.js \
    && curl -fsSL \
        "https://unpkg.com/meshoptimizer@1.3.0/meshopt_decoder.cjs" \
        -o /preview/site/vendor/meshopt_decoder.js
# ^ model-viewer has no built-in default for the EXT_meshopt_compression
# decoder; index.html points it at this vendored copy.

ENV SITE_DIR=/preview/site \
    HARDWARE_DIR=/work/hardware \
    ENCLOSURE_DIR=/work/enclosure \
    PORT=8787

EXPOSE 8787

ENTRYPOINT ["/preview/scripts/entrypoint.sh"]

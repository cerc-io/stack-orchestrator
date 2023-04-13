# Kubo (IPFS)

The Kubo stack currently uses the native IPFS docker image, therefore a single command will do:

```
laconic-so --stack kubo deploy up
```

If running locally, visit: http://localhost:5001/webui and explore the functionality of the WebUI.

If running in the cloud, visit `IP:5001/webui` and you'll likely see this error: "Could not connect to the IPFS API". To fix it:

1. Get the container name with `docker ps`:

2. Go into the container (replace with your container name):

```
docker exec -it laconic-dbbf5498fd7d322930b9484121a6a5f4-ipfs-1 sh
```

3. Enable CORS as described in point 2 of the error message. Copy/paste/run each line in sequence, then run `exit` to exit the container.

4. Restart the container:

```
laconic-so --stack kubo deploy down
laconic-so --stack kubo deploy up
```

5. Refresh the `IP:5001/webui` URL in your browser, you should now be connected to IPFS.

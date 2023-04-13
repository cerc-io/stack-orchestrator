# Kubo (IPFS)

The Kubo stack currently uses the native IPFS docker image, therefore a single command will do:

```
laconic-so --stack kubo deploy up
```

If running locally, visit: [localhost:5001/webui](localhost:5001/webui) and explore the functionality of the WebUI.

If running in the cloud, visit `IP:5001/webui` and you'll likely see this error: "Could not connect to the IPFS API". To fix it:

1. Get the container name:

```
docker ps
```

```
4dc93dea88df   ipfs/kubo:master-2023-02-20-714a968   "/sbin/tini -- /usr/…"   51 minutes ago   Up 51 minutes (healthy)   0.0.0.0:4001->4001/tcp, 0.0.0.0:5001->5001/tcp, 4001/udp, 0.0.0.0:8080->8080/tcp, 8081/tcp   laconic-dbbf5498fd7d322930b9484121a6a5f4-ipfs-1
```

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

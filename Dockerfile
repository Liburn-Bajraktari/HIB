# Stage 1: Build Node.js environment
FROM node:14 as node-builder

# Set the working directory
WORKDIR /usr/src/app

# Copy package.json and package-lock.json for npm install
COPY package*.json ./

# Install npm dependencies
RUN npm install

# Copy the rest of the working directory contents into the container at /usr/src/app
COPY . .

# Stage 2: Build Python environment
FROM python:3.9

# Set the working directory
WORKDIR /usr/src/app

# Copy the requirements file into the container at /usr/src/app
COPY requirements.txt .

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Node.js application from the previous stage
COPY --from=node-builder /usr/src/app /usr/src/app

# Expose the port the app runs on (optional, based on your Node.js script)
EXPOSE 3000

# Run the application
CMD ["python", "Audio Bot.py"]

const YouTube = require('youtube-sr').default;
const ytdl = require('ytdl-core');
const fs = require('fs');

// Extract search term and filename from command line arguments
let search_term = process.argv[2];
let filename = process.argv[3];

// Store the name of the last downloaded file
let lastFile;

// Specify the log file
let logFile = 'Downloader_NodeJS.log';

function log(message) {
    let timestamp = new Date().toLocaleString();
    let logMessage = `${timestamp} ${message}`;
    console.log(logMessage);
    fs.appendFileSync(logFile, logMessage + '\n');
}

YouTube.search(search_term, { limit: 1 })
    .then(results => {
        if (results && results[0]) {
            let result = results[0];

            if (fs.existsSync(filename)) {
                // If the file already exists, don't re-download it
                log(`File ${filename} already exists, skipping download.`);
            } else {
                // If a different file was downloaded last time, delete it
                if (lastFile && lastFile !== filename) {
                    try {
                        fs.unlinkSync(lastFile);
                    } catch (err) {
                        log(`Failed to delete file ${lastFile}: ${err.message}`);
                    }
                }

                // Start downloading the file
                ytdl(result.url, {filter: 'audioonly'})
                    .pipe(fs.createWriteStream(filename))
                    .on('finish', () => {
                        // Update the name of the last downloaded file
                        lastFile = filename;
                    });
            }
        }
    })
    .catch(err => log(err.message));

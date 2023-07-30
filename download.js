const YouTube = require('youtube-sr').default;
const ytdl = require('ytdl-core');
const fs = require('fs');
const path = require('path');

// Extract search term and filename from command line arguments
let search_term = process.argv[2];

// Download directory
const download_directory = 'downloads';

// Make sure download directory exists
if (!fs.existsSync(download_directory)) {
    fs.mkdirSync(download_directory);
}

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

            // Construct the filename with the video title
            let filename = `${result.title.replace(/[\/:*?"<>|]/g, '')}.mp3`;
            let filepath = path.join(download_directory, filename);

            // Function to write the filename
            const writeFilename = () => {
                let filenamePath = path.join(download_directory, 'filename.txt');
                fs.writeFileSync(filenamePath, filepath);
                log(`Successfully wrote filename to filename.txt: ${filepath}`);
            };

            if (fs.existsSync(filepath)) {
                // If the file already exists, don't re-download it
                log(`File ${filepath} already exists, skipping download.`);
                writeFilename(); // Write the filename even if skipping download
            } else {
                // Start downloading the file
                let downloadStream = ytdl(result.url, { filter: 'audioonly' });

                downloadStream.on('error', err => {
                    log(`Error downloading video: ${err}`);
                });

                downloadStream.pipe(fs.createWriteStream(filepath))
                    .on('finish', () => {
                        writeFilename();
                    });
            }
        }
    })
    .catch(err => {
        if (err.statusCode === 410) {
          log(`Error downloading video (Status code 410): ${search_term}`);
        } else {
          log(err.message);
        }
    });

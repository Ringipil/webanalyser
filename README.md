# webanalyzer
The webanalyzer webapp has the following functionality:
1. Web interface:
- provides a simple web interface that allows the user to enter a web page URL for analysis
2. Content extraction:
- Visits the entered URL and extracts:
- The main text content of the page
- The meta description (meta description)
- The keywords (meta keywords)
3. Hyperlink extraction:
- Extracts all hyperlinks (<a> tags) on the page along with their text and URLs
4. Content analysis:
- Analyzes the main text content of the page:
- Calculates the number of words
- Extracts the 10 most common words (excluding stop words)
- Generates a word cloud or bar chart for visualization
5. Visualizes on a link graph:
- Creates a graph where:
- Nodes represent URLs
- The edges represent the links between them
- Visualizes the graph
6. Validate hyperlinks:
- Check the validity of all extracted links by sending HTTP requests to get their status (e.g. 200, 404, 500).
7. Generate a report:
- Generatea a PDF report (file to download) that contains:
- Summary of the extracted information
- Word cloud or bar chart
- Visualization of the link graph
8. Saves the results:
- Saves the extracted data in a CSV file (to download) with columns: "Link text", "URL", and "HTTP status".

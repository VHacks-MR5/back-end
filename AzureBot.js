/*-----------------------------------------------------------------------------
A simple echo bot for the Microsoft Bot Framework. 
-----------------------------------------------------------------------------*/

var restify = require('restify');
var builder = require('botbuilder');
var botbuilder_azure = require("botbuilder-azure");
var http = require("http");
var https = require("https");
var fs = require('fs');
var querystring = require('querystring');

var missingPersonImage = {}; 
var missingPersonName = '';
var missingPersonAge = '';
var imageSource = '';
var missingPersonNationality = '';
var missingPersonUploaderName = '';
var missingPersonUploaderRelation = '';
var missingPersonUploaderContact = '';
 
// Setup Restify Server
var server = restify.createServer();
server.listen(process.env.port || process.env.PORT || 3978, function () {
   console.log('%s listening to %s', server.name, server.url); 
});
  
// Create chat connector for communicating with the Bot Framework Service
var connector = new builder.ChatConnector({
    appId: process.env.MicrosoftAppId,
    appPassword: process.env.MicrosoftAppPassword,
    openIdMetadata: process.env.BotOpenIdMetadata 
});

// Listen for messages from users 
server.post('/api/messages', connector.listen());

/*----------------------------------------------------------------------------------------
* Bot Storage: This is a great spot to register the private state storage for your bot. 
* We provide adapters for Azure Table, CosmosDb, SQL Azure, or you can implement your own!
* For samples and documentation, see: https://github.com/Microsoft/BotBuilder-Azure
* ---------------------------------------------------------------------------------------- */

var tableName = 'botdata';
var azureTableClient = new botbuilder_azure.AzureTableClient(tableName, process.env['AzureWebJobsStorage']);
var tableStorage = new botbuilder_azure.AzureBotStorage({ gzipData: false }, azureTableClient);

var inMemoryStorage = new builder.MemoryBotStorage();
// Create your bot with a function to receive messages from the user
// This is a reservation bot that has a menu of offerings.
// Main menu
var menuItems = { 
    "Search for person": {
        item: "search"
    },
    "Upload person to database": {
        item: "upload"
    }
};

var contactmenu = {
    "Apply to Contact": {
        item: "contact"
    },
    "Return to Main Menu": {
        item: "mainMenu"
    }
};

var bot = new builder.UniversalBot(connector, [
    function(session){
        session.send("Welcome to Vinculum Bot!");
        session.beginDialog("mainMenu");
    }
]).set('storage', inMemoryStorage); // Register in-memory storage 

// Display the main menu and start a new request depending on user input.
bot.dialog("mainMenu", [
    function(session){
        missingPersonImage = {};
        missingPersonName = '';
        missingPersonAge = '';
        imageSource = '';
        missingPersonNationality = '';
        missingPersonUploaderName = '';
        missingPersonUploaderRelation = '';
        missingPersonUploaderContact = '';
        builder.Prompts.choice(session, "Enter the number of the service you wish to use: ", menuItems);
    },
    function(session, results){
        if(results.response){
            session.beginDialog(menuItems[results.response.entity].item);
        }
    }
])
.triggerAction({
    // The user can request this at any time.
    // Once triggered, it clears the stack and prompts the main menu again.
    matches: /^main menu$/i
});

// This dialog helps the user make a dinner reservation.
bot.dialog('search', [
    function (session) {
        session.send("Please upload or take a photo and we will find the best match");
        session.beginDialog('askForDateTime');
    },
    function(session){
        session.endDialog();
    }
])
.triggerAction({
    matches: /^search$/i
});
// Dialog to ask for a date and time
bot.dialog('askForDateTime', [
    function (session) {
        // builder.Prompts.time(session, "Please provide a reservation date and time (e.g.: June 6th at 5pm)");
        var reply = new builder.Message().address(session.message.address);

    var msg = session.message; 
    console.log(msg.text);
    if (msg.attachments && msg.attachments.length > 0) {
     // Echo back attachment
     var attachment = msg.attachments[0];  
     var http_url = attachment.contentUrl.slice(0, 5) + attachment.contentUrl.slice(5, attachment.contentUrl.length);
     console.log(http_url);
    var req = http.get('http://23.101.170.100:5000/match/app?url=' + http_url, function(res) {
      // console.log('STATUS: ' + res.statusCode);
      // console.log('HEADERS: ' + JSON.stringify(res.headers));
    
      // Buffer the body entirely for processing as a whole.
      var bodyChunks = [];
      res.on('data', function(chunk) {
        bodyChunks.push(chunk);
      }).on('end', function() {
        var body = Buffer.concat(bodyChunks);
        var obj = JSON.parse(body); 
        console.log(obj);
        missingPersonName = obj.messages[1].data[1];
        missingPersonNationality = obj.messages[1].data[5];
        missingPersonAge = obj.messages[1].data[3];
        imageSource = obj.messages[1].data[7];
        missingPersonUploaderName = obj.messages[1].data[8];
        missingPersonUploaderRelation = obj.messages[1].data[9];
        missingPersonUploaderContact = obj.messages[1].data[10];
        missingPersonImage = 
                {
                    contentType:  attachment.contentType,
                    contentUrl: obj.messages[2].attachment.payload.url,
                    name:  attachment.name
                };
                console.log(obj.messages[2].attachment.payload.url);
        session.send({
            text: "This is the best match. The " + obj.messages[0].text.toLowerCase(),
            attachments: [
                {
                    contentType:  attachment.contentType,
                    contentUrl: obj.messages[2].attachment.payload.url,
                    name:  attachment.name
                }
            ]
        }); 
        builder.Prompts.choice(session, "What would you like to do next?  ", contactmenu); 
      });
    });
    req.on('error', function(e) {
      console.log('ERROR: ' + e.message);
    });
    }
    }, 
     function(session, results){
         if(results.response){
            session.beginDialog(contactmenu[results.response.entity].item);
        }
    }
]);

bot.dialog('upload', [
    function(session){
        builder.Prompts.attachment(session, "Please upload an image");
    },
    function (session, results) {
        session.dialogData.image = results.response;
        builder.Prompts.text(session, "Name of missing person?");
    },
    function (session, results) {
        session.dialogData.name = results.response;
        builder.Prompts.number(session, "Age?");
    },
     function (session, results) {
        session.dialogData.age = results.response;
        builder.Prompts.text(session, "Nationality?");
    },
    function (session, results) {
        session.dialogData.country = results.response;
        builder.Prompts.text(session, "Your name?");
    },
    function (session, results) {
        session.dialogData.searcher_name = results.response;
        builder.Prompts.text(session, "Your relation to missing person?");
    },
    function (session, results) {
        session.dialogData.searcher_relation = results.response;
        builder.Prompts.text(session, "Your contact info?");
    },
    function(session, results){
        session.dialogData.searcher_contact = results.response; 
        console.log('Uploaded image url: ' + session.dialogData.image[0].contentUrl); 
        var image_attachment =
                {
                    contentType: session.dialogData.image[0].contentType,
                    contentUrl: session.dialogData.image[0].contentUrl,
                    name: session.dialogData.image[0].name
                }
            ;
        var msg = "The following information and attached image have been uploaded to our system: \n"
        +  " \n Name: " + session.dialogData.name + 
        " \n Age: " + session.dialogData.age +
        " \n Nationality: " + session.dialogData.country;
        session.send({
            text: msg,
            attachments: [image_attachment]
        });
        var req = http.get('http://23.101.170.100:5000/upload/app?url=' + session.dialogData.image[0].contentUrl + '&fullname=' + session.dialogData.name + '&age=' + session.dialogData.age + '&nationality=' + session.dialogData.country 
           + '&uploader_name=' + session.dialogData.searcher_name + '&uploader_relation=' + session.dialogData.searcher_relation + '&uploader_contact_info=' + session.dialogData.searcher_contact + '&source=' + 'Independent party', function(res) {
          console.log('STATUS: ' + res.statusCode);
          console.log('HEADERS: ' + JSON.stringify(res.headers));
       });
        session.send("Type `Main Menu` to return to the main menu");
    }
])
.triggerAction({
    matches: /^upload$/i
});

bot.dialog('contact', [
     function(session){
        builder.Prompts.attachment(session, "Please upload a photo of yourself:");
    },
    function(session, results){
        session.dialogData.searcher_image = results.response;
        builder.Prompts.text(session, "Please enter your name ");
    },
    function (session, results) {
        session.dialogData.searcher_name = results.response;
        builder.Prompts.number(session, "Enter your age:");
    },
    function (session, results) {
        session.dialogData.searcher_age = results.response;
        builder.Prompts.text(session, "Relation to missing person:");
    },
    function (session, results) {
        session.dialogData.relation = results.response;
        builder.Prompts.text(session, "Contact info (submit a phone number or email)");
    },
     function (session, results) {
        session.dialogData.contactInfo = results.response;
        builder.Prompts.text(session, "Any additional information?");
    },
    function(session, results){
        session.dialogData.notes = results.response;
        var msg = "Thank you for submitting the application! We will process your information and reach out when we have an update. \n"
        +  " \n Name: " + session.dialogData.searcher_name + 
        " \n Age: " + session.dialogData.searcher_age +
        " \n Relation to missing person: " + session.dialogData.relation +
        " \n Contact Info: " + session.dialogData.contactInfo + 
        "\n Additional Info: " + session.dialogData.notes;
        session.send({
            text: msg, 
            attachments:[session.dialogData.searcher_image[0],missingPersonImage]
        });
        
        console.log(missingPersonName, missingPersonAge, imageSource, missingPersonNationality
,missingPersonUploaderName,missingPersonUploaderRelation,missingPersonUploaderContact);
        var request_data = JSON.stringify({
          "searcher_name": session.dialogData.searcher_name , 
          "searcher_age": session.dialogData.searcher_age.toString(),
          "searcher_relation": session.dialogData.relation,
          "searcher_location": '',
          "searcher_contact": session.dialogData.contactInfo, 
          "searcher_info": session.dialogData.notes, 
          "searcher_image":  session.dialogData.searcher_image[0].contentUrl,
          "missing_person_name": missingPersonName,
          "missing_person_age": missingPersonAge.toString(),
          "missing_person_image_source": imageSource,
          "missing_person_nationality": missingPersonNationality,
          "missing_person_image": missingPersonImage.contentUrl, 
          "missing_person_uploader_name": missingPersonUploaderName,
          "missing_person_uploader_relation": (missingPersonUploaderRelation != null ? missingPersonUploaderRelation : ''),
          "missing_person_contact": (missingPersonUploaderContact != null ? missingPersonUploaderContact : '')
        });
        
        var post_options = {
            hostname: '23.101.170.100',
            port    : '5000',
            path    : '/email',
            method  : 'POST',
            headers : {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(request_data)
            }
        };
        
        var post_req = http.request(post_options, function (res) {
            console.log('Request post options: ' + post_options['headers']['Content-Type']);
            console.log('STATUS: ' + res.statusCode);
            console.log('HEADERS: ' + JSON.stringify(res.headers));
            res.setEncoding('utf8');
            res.on('data', function (chunk) {
                console.log('Response: ', chunk);
            });
        });
        
        post_req.on('error', function(e) {
            console.log('problem with request: ' + e.message);
        });
        
        post_req.write(request_data);
        post_req.end();
        missingPersonImage = {};
        missingPersonName = '';
        missingPersonAge = '';
        imageSource = '';
        missingPersonNationality = '';
        missingPersonUploaderName = '';
        missingPersonUploaderRelation = '';
        missingPersonUploaderContact = '';
        session.send("Type `Main Menu` to return to the main menu");
    }
])
.triggerAction({
    matches: /^contact/i
});

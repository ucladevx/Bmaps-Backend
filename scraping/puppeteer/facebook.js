const puppeteer = require('puppeteer');


const USERNAME_SELECTOR = '#email'
const PASSWORD_SELECTOR = '#pass'
const LOGIN_SELECTOR = '#loginbutton'

let anchorHref;

async function run() {

    // launch puppeteer
    const browser = await puppeteer.launch({
        headless: false, 
        args: ['--disable-notifications']
    });
    
    // log in to facebook
    const page = await browser.newPage();
    await page.goto('https://facebook.com');
    
    await page.click(USERNAME_SELECTOR);
    await page.keyboard.type("mappening2019@hotmail.com");
    
    await page.click(PASSWORD_SELECTOR);
    await page.keyboard.type("Mappening 2019");
    
    await page.click(LOGIN_SELECTOR);
    await page.waitForNavigation();
    
    // first endpoint
    await page.goto('https://www.facebook.com/search/events/?q=ucla');
    
    // turn off asking to show notifications
    page.on('dialog', async dialog => {
        console.log(dialog.message());
        await dialog.dismiss();
    })
    

    let handles = [];

    let keepCalling = true;
    let keepCallingTimeout = setTimeout(function () {
        keepCalling = false;
    }, 30000);

    // Date: Any Date
    
    while(true) {
        
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');
        
        handles = await page.$$('.fbEventAttachmentCTAButton');
        

        console.log(handles.length);

        if(handles.length != 0) {
            keepCalling = true;
            clearTimeout(keepCallingTimeout);
            keepCallingTimeout = setTimeout(function () {
                keepCalling = false;
            }, 30000);
        }

        // if there are no handles just go to the next page
        if (handles.length == 0 && keepCalling == false) {
            break;
        }

        for (let interested of handles)
            await interested.click();

    }

    keepCalling = true;
    keepCallingTimeout = setTimeout(function () {
        keepCalling = false;
    }, 30000);

    
     
    // Date: Today

    dateRangeAnchors = await page.$$('._4f3b');
    console.log(dateRangeAnchors);
    anchorHref = await page.evaluate(anchor => anchor.getAttribute('href'), dateRangeAnchors[5]);
    console.log(anchorHref);
    await page.goto(anchorHref);


    while(true) {
        
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');
        
        handles = await page.$$('.fbEventAttachmentCTAButton');
        

        console.log(handles.length);

        if(handles.length != 0) {
            keepCalling = true;
            clearTimeout(keepCallingTimeout);
            keepCallingTimeout = setTimeout(function () {
                keepCalling = false;
            }, 30000);
        }

        // if there are no handles just go to the next page
        if (handles.length == 0 && keepCalling == false) {
            break;
        }

        for (let interested of handles)
            await interested.click();

    }


    keepCalling = true;
    keepCallingTimeout = setTimeout(function () {
        keepCalling = false;
    }, 30000);

    // Date: Tomorrow

    dateRangeAnchors = await page.$$('._4f3b');
    console.log(dateRangeAnchors);
    anchorHref = await page.evaluate(anchor => anchor.getAttribute('href'), dateRangeAnchors[6]);
    console.log(anchorHref);
    await page.goto(anchorHref);

    while(true) {
        
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');
        
        handles = await page.$$('.fbEventAttachmentCTAButton');
        

        console.log(handles.length);

        if(handles.length != 0) {
            keepCalling = true;
            clearTimeout(keepCallingTimeout);
            keepCallingTimeout = setTimeout(function () {
                keepCalling = false;
            }, 30000);
        }

        // if there are no handles just go to the next page
        if (handles.length == 0 && keepCalling == false) {
            break;
        }

        for (let interested of handles)
            await interested.click();

    }


    keepCalling = true;
    keepCallingTimeout = setTimeout(function () {
        keepCalling = false;
    }, 30000);

    // Date: This Week

    dateRangeAnchors = await page.$$('._4f3b');
    console.log(dateRangeAnchors);
    anchorHref = await page.evaluate(anchor => anchor.getAttribute('href'), dateRangeAnchors[7]);
    console.log(anchorHref);
    await page.goto(anchorHref);

    while(true) {
        
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');
        
        handles = await page.$$('.fbEventAttachmentCTAButton');
        

        console.log(handles.length);

        if(handles.length != 0) {
            keepCalling = true;
            clearTimeout(keepCallingTimeout);
            keepCallingTimeout = setTimeout(function () {
                keepCalling = false;
            }, 30000);
        }

        // if there are no handles just go to the next page
        if (handles.length == 0 && keepCalling == false) {
            break;
        }

        for (let interested of handles)
            await interested.click();

    }


    keepCalling = true;
    keepCallingTimeout = setTimeout(function () {
        keepCalling = false;
    }, 30000);

    // Date: This Weekend

    dateRangeAnchors = await page.$$('._4f3b');
    console.log(dateRangeAnchors);
    anchorHref = await page.evaluate(anchor => anchor.getAttribute('href'), dateRangeAnchors[8]);
    console.log(anchorHref);
    await page.goto(anchorHref);

    while(true) {
        
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');
        
        handles = await page.$$('.fbEventAttachmentCTAButton');
        

        console.log(handles.length);

        if(handles.length != 0) {
            keepCalling = true;
            clearTimeout(keepCallingTimeout);
            keepCallingTimeout = setTimeout(function () {
                keepCalling = false;
            }, 30000);
        }

        // if there are no handles just go to the next page
        if (handles.length == 0 && keepCalling == false) {
            break;
        }

        for (let interested of handles)
            await interested.click();

    }


    keepCalling = true;
    keepCallingTimeout = setTimeout(function () {
        keepCalling = false;
    }, 30000);

    // Date: This Weekend

    dateRangeAnchors = await page.$$('._4f3b');
    console.log(dateRangeAnchors);
    anchorHref = await page.evaluate(anchor => anchor.getAttribute('href'), dateRangeAnchors[9]);
    console.log(anchorHref);
    await page.goto(anchorHref);

    while(true) {
        
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');
        
        handles = await page.$$('.fbEventAttachmentCTAButton');
        

        console.log(handles.length);

        if(handles.length != 0) {
            keepCalling = true;
            clearTimeout(keepCallingTimeout);
            keepCallingTimeout = setTimeout(function () {
                keepCalling = false;
            }, 30000);
        }

        // if there are no handles just go to the next page
        if (handles.length == 0 && keepCalling == false) {
            break;
        }

        for (let interested of handles)
            await interested.click();

    }



    browser.close();

}

run();
const puppeteer = require('puppeteer');
// const CREDS = require('./fbcreds');

const USERNAME_SELECTOR = '#email'
const PASSWORD_SELECTOR = '#pass'
const LOGIN_SELECTOR = '#loginbutton'
const TEST_SELECTOR_ONE = 'body'
//#u_ps_fetchstream_3_4_a > a
//#u_ps_fetchstream_3_4_c > a
//#u_ps_fetchstream_3_4_e > a
//#u_ps_0_4_b > a
//#u_ps_0_4_z > a
//#u_ps_0_4_s > a

function nextSelector(c) {
    return String.fromCharCode(c.charCodeAt(0) + 1);
}

function sleep(ms) {
    return new Promise(resolve => {
        setTimeout(resolve, ms)
    })
}

function delay(time) {
    return new Promise(function(resolve) { 
        setTimeout(resolve, time)
    });
 }

async function clickButtons(page) {
    while(true) {        
        
        
        // scroll to the bottom first
        await page.evaluate(_ => {
            window.scrollBy(0, window.innerHeight);
        });

        await autoScroll(page);
        
        handles = await page.$$('.fbEventAttachmentCTAButton');
        
        console.log(handles.length);

        // handles = await page.$$('.fbEventAttachmentCTAButton');

        //await sleep(5000);

        // if there are no handles just go to the next page
        if (handles.length == 0) {
            break;
        }

        for (let interested of handles)
            await interested.click();

    }
}

async function autoScroll(page){
    await page.evaluate(async () => {
        await new Promise((resolve, reject) => {
            var totalHeight = 0;
            var distance = 100;
            var timer = setInterval(() => {
                var scrollHeight = document.body.scrollHeight;
                window.scrollBy(0, distance);
                totalHeight += distance;

                if(totalHeight >= scrollHeight){
                    clearInterval(timer);
                    resolve();
                }
            }, 100);
        });
    });
}

async function run() {

    
    
    const browser = await puppeteer.launch({
        headless: false, 
        args: ['--disable-notifications']
    });
    
    const page = await browser.newPage();
    await page.goto('https://facebook.com');
    
    await page.click(USERNAME_SELECTOR);
    await page.keyboard.type("mappening2019@hotmail.com");
    
    await page.click(PASSWORD_SELECTOR);
    await page.keyboard.type("Mappening 2019");
    
    await page.click(LOGIN_SELECTOR);
    await page.waitForNavigation();
    
    await page.goto('https://www.facebook.com/search/events/?q=ucla');
    
    // turn off asking to show notifications
    page.on('dialog', async dialog => {
        console.log(dialog.message());
        await dialog.dismiss();
    })
    /*let selec = 'b'
    while (selec <= 'z') {
        let tempSelec = TEST_SELECTOR_ONE.replace("SELECTOR", selec);
        selec = nextSelector(selec);
        if (await page.$(tempSelec) != null) {
            await page.click(tempSelec, selec);
        }
        else {
            console.log('not found' + tempSelec)
        }

    }*/
    //page.click(body);
    /*let temp = await page.evaluate(() => {
        console.log("entered");
        let interesteds = $('_42ft _4jy0 fbEventAttachmentCTAButton _522u _4jy3 _517h _51sy').toArray();
        for (i = 0; i < interesteds.length; i++) {
            $(elements[i]).click();
        }
    });*/
    // let handles = await page.$$('._42ft._4jy0.fbEventAttachmentCTAButton._522u._4jy3._517h._51sy');
    

    let handles = [];

    let keepCalling = true;
    let keepCallingTimeout = setTimeout(function () {
        keepCalling = false;
    }, 60000);

    // Date: Any Date
    while(true) {        
        
        
        // scroll to the bottom first
        await page.evaluate(_ => {
            window.scrollBy(0, window.innerHeight);
        });

        await autoScroll(page);
        
        handles = await page.$$('.fbEventAttachmentCTAButton');
        
        console.log(handles.length);

        if(handles.length != 0) {
            keepCalling = true;
            clearTimeout(keepCallingTimeout);
            keepCallingTimeout = setTimeout(function () {
                keepCalling = false;
            }, 60000);
        }

        // handles = await page.$$('.fbEventAttachmentCTAButton');

        //await sleep(5000);

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
    }, 60000);

    // Date: Today

    await page.goto('https://www.facebook.com/search/events/?q=ucla&epa=FILTERS&filters=eyJycF9ldmVudHNfZGF0ZSI6IntcIm5hbWVcIjpcImZpbHRlcl9ldmVudHNfZGF0ZVwiLFwiYXJnc1wiOlwiMjAxOS0wNC0xOVwifSJ9');

    while(true) {        
        
        
        // scroll to the bottom first
        await page.evaluate(_ => {
            window.scrollBy(0, window.innerHeight);
        });

        await autoScroll(page);
        
        handles = await page.$$('.fbEventAttachmentCTAButton');
        
        console.log(handles.length);

        if(handles.length != 0) {
            keepCalling = true;
            clearTimeout(keepCallingTimeout);
            keepCallingTimeout = setTimeout(function () {
                keepCalling = false;
            }, 60000);
        }

        // handles = await page.$$('.fbEventAttachmentCTAButton');

        //await sleep(5000);

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
    }, 60000);

    // Date: Tomorrow

    await page.goto('https://www.facebook.com/search/events/?q=ucla&epa=FILTERS&filters=eyJycF9ldmVudHNfZGF0ZSI6IntcIm5hbWVcIjpcImZpbHRlcl9ldmVudHNfZGF0ZVwiLFwiYXJnc1wiOlwiMjAxOS0wNC0yMFwifSJ9&ref=side_filter');

    while(true) {        
        
        
        // scroll to the bottom first
        await page.evaluate(_ => {
            window.scrollBy(0, window.innerHeight);
        });

        await autoScroll(page);
        
        handles = await page.$$('.fbEventAttachmentCTAButton');
        
        console.log(handles.length);

        if(handles.length != 0) {
            keepCalling = true;
            clearTimeout(keepCallingTimeout);
            keepCallingTimeout = setTimeout(function () {
                keepCalling = false;
            }, 60000);
        }

        // handles = await page.$$('.fbEventAttachmentCTAButton');

        //await sleep(5000);

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
    }, 60000);

    // Date: This Week

    await page.goto('https://www.facebook.com/search/events/?q=ucla&epa=FILTERS&filters=eyJycF9ldmVudHNfZGF0ZSI6IntcIm5hbWVcIjpcImZpbHRlcl9ldmVudHNfZGF0ZVwiLFwiYXJnc1wiOlwiMjAxOS0wNC0xNX4yMDE5LTA0LTIxXCJ9In0%3D&ref=side_filter');

    while(true) {        
        
        
        // scroll to the bottom first
        await page.evaluate(_ => {
            window.scrollBy(0, window.innerHeight);
        });

        await autoScroll(page);
        
        handles = await page.$$('.fbEventAttachmentCTAButton');
        
        console.log(handles.length);

        if(handles.length != 0) {
            keepCalling = true;
            clearTimeout(keepCallingTimeout);
            keepCallingTimeout = setTimeout(function () {
                keepCalling = false;
            }, 60000);
        }

        // handles = await page.$$('.fbEventAttachmentCTAButton');

        //await sleep(5000);

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
    }, 60000);

    // Date: This Weekend

    await page.goto('https://www.facebook.com/search/events/?q=ucla&epa=FILTERS&filters=eyJycF9ldmVudHNfZGF0ZSI6IntcIm5hbWVcIjpcImZpbHRlcl9ldmVudHNfZGF0ZVwiLFwiYXJnc1wiOlwiMjAxOS0wNC0yMH4yMDE5LTA0LTIxXCJ9In0%3D');

    while(true) {        
        
        
        // scroll to the bottom first
        await page.evaluate(_ => {
            window.scrollBy(0, window.innerHeight);
        });

        await autoScroll(page);
        
        handles = await page.$$('.fbEventAttachmentCTAButton');
        
        console.log(handles.length);

        if(handles.length != 0) {
            keepCalling = true;
            clearTimeout(keepCallingTimeout);
            keepCallingTimeout = setTimeout(function () {
                keepCalling = false;
            }, 60000);
        }

        // handles = await page.$$('.fbEventAttachmentCTAButton');

        //await sleep(5000);

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
    }, 60000);

    // Date: This Weekend

    await page.goto('https://www.facebook.com/search/events/?q=ucla&epa=FILTERS&filters=eyJycF9ldmVudHNfZGF0ZSI6IntcIm5hbWVcIjpcImZpbHRlcl9ldmVudHNfZGF0ZVwiLFwiYXJnc1wiOlwiMjAxOS0wNC0yMn4yMDE5LTA0LTI4XCJ9In0%3D');

    while(true) {        
        
        
        // scroll to the bottom first
        await page.evaluate(_ => {
            window.scrollBy(0, window.innerHeight);
        });

        await autoScroll(page);
        
        handles = await page.$$('.fbEventAttachmentCTAButton');
        
        console.log(handles.length);

        if(handles.length != 0) {
            keepCalling = true;
            clearTimeout(keepCallingTimeout);
            keepCallingTimeout = setTimeout(function () {
                keepCalling = false;
            }, 60000);
        }

        // handles = await page.$$('.fbEventAttachmentCTAButton');

        //await sleep(5000);

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
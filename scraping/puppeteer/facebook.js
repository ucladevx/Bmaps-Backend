const puppeteer = require('puppeteer');
const CREDS = require('./fbcreds');

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

async function run() {
    const browser = await puppeteer.launch({
        headless: true
    });

    const page = await browser.newPage();
    await page.goto('https://facebook.com');

    await page.click(USERNAME_SELECTOR);
    await page.keyboard.type(CREDS.fbusername);

    await page.click(PASSWORD_SELECTOR);
    await page.keyboard.type(CREDS.fbpassword);

    await page.click(LOGIN_SELECTOR);
    await page.waitForNavigation();

    await page.goto('https://www.facebook.com/search/events/?q=ucla');
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
    let handles = await page.$$('._42ft._4jy0.fbEventAttachmentCTAButton._522u._4jy3._517h._51sy');
    console.log(handles.length);
    //await sleep(5000);


    for (let interested of handles)
        await interested.click();

    browser.close();

}

run();
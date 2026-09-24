/**
 * Birthday reminders from Google Contacts to a private Telegram chat.
 *
 * Runs once a day, reads birthdays through the People API, and sends one
 * message when a contact has a birthday in REMIND_DAYS days.
 *
 * Secrets live in Script Properties, never in this file:
 *   TELEGRAM_BOT_TOKEN        shared Telegram bot token
 *   PERSONAL_CHAT_ID_TELEGRAM numeric ID of the private chat
 *   TELEGRAM_API_BASE_URL     optional, defaults to https://api.telegram.org
 */

/** Days before a birthday that trigger a reminder. 0 means the day itself. */
const REMIND_DAYS = [3, 0];

/** Hour of the day the trigger fires, in the script time zone. */
const TRIGGER_HOUR = 9;

const TOKEN_PROPERTY = 'TELEGRAM_BOT_TOKEN';
const CHAT_ID_PROPERTY = 'PERSONAL_CHAT_ID_TELEGRAM';
const BASE_URL_PROPERTY = 'TELEGRAM_API_BASE_URL';
const LAST_RUN_PROPERTY = 'LAST_RUN_DATE';

const DEFAULT_API_BASE_URL = 'https://api.telegram.org';
const MESSAGE_LIMIT = 4000;
const PAGE_SIZE = 1000;
const MILLIS_PER_DAY = 24 * 60 * 60 * 1000;

/**
 * Entry point for the daily trigger.
 */
function dailyBirthdayCheck() {
  const timeZone = Session.getScriptTimeZone();
  const today = startOfToday_(timeZone);
  const stamp = Utilities.formatDate(today, timeZone, 'yyyy-MM-dd');
  const properties = PropertiesService.getScriptProperties();

  if (properties.getProperty(LAST_RUN_PROPERTY) === stamp) {
    console.log(`Already checked ${stamp}, skipping.`);
    return;
  }

  const matches = findMatches_(fetchBirthdays_(), today);
  if (matches.length) {
    sendTelegram_(buildMessage_(matches));
    console.log(`Reported ${matches.length} birthday(s).`);
  } else {
    console.log('No birthdays to report.');
  }

  // Written last so a failed send retries on the next run.
  properties.setProperty(LAST_RUN_PROPERTY, stamp);
}

/**
 * Installs the daily trigger, replacing any trigger for the same handler.
 * Run once by hand after setting the script properties.
 */
function installDailyTrigger() {
  ScriptApp.getProjectTriggers()
    .filter((trigger) => trigger.getHandlerFunction() === 'dailyBirthdayCheck')
    .forEach((trigger) => ScriptApp.deleteTrigger(trigger));

  ScriptApp.newTrigger('dailyBirthdayCheck')
    .timeBased()
    .everyDays(1)
    .atHour(TRIGGER_HOUR)
    .create();

  console.log(`Daily trigger installed for ${TRIGGER_HOUR}:00 ${Session.getScriptTimeZone()}.`);
}

/**
 * Logs the message that would be sent today without sending anything.
 */
function previewBirthdays() {
  const today = startOfToday_(Session.getScriptTimeZone());
  const matches = findMatches_(fetchBirthdays_(), today);
  console.log(matches.length ? buildMessage_(matches) : 'No birthdays to report.');
}

/**
 * Sends a throwaway message to confirm the token and chat ID work.
 */
function sendTestMessage() {
  sendTelegram_('<b>Birthdays</b>\n\nTest message from the birthday reminder script.');
}

/**
 * Reads every contact that has a birthday with a month and a day.
 *
 * @return {!Array<{name: string, month: number, day: number, year: ?number}>}
 */
function fetchBirthdays_() {
  const contacts = [];
  let pageToken;

  do {
    const response = People.People.Connections.list('people/me', {
      personFields: 'names,birthdays',
      pageSize: PAGE_SIZE,
      pageToken: pageToken,
    });

    (response.connections || []).forEach((person) => {
      const name = displayName_(person);
      const date = birthdayDate_(person);
      if (!name || !date) {
        return;
      }
      contacts.push({
        name: name,
        month: date.month,
        day: date.day,
        // Contacts stored without a year omit it; some sources use a placeholder.
        year: date.year && date.year > 1900 ? date.year : null,
      });
    });

    pageToken = response.nextPageToken;
  } while (pageToken);

  console.log(`Found ${contacts.length} contact(s) with a birthday.`);
  return contacts;
}

/**
 * @param {!Object} person
 * @return {string}
 */
function displayName_(person) {
  const names = person.names || [];
  for (let index = 0; index < names.length; index += 1) {
    const name = names[index].displayName || names[index].givenName;
    if (name) {
      return name;
    }
  }
  return '';
}

/**
 * Returns the first usable birthday. Merged contacts can carry several.
 *
 * @param {!Object} person
 * @return {?{month: number, day: number, year: (number|undefined)}}
 */
function birthdayDate_(person) {
  const birthdays = person.birthdays || [];
  for (let index = 0; index < birthdays.length; index += 1) {
    const date = birthdays[index].date;
    if (date && date.month && date.day) {
      return date;
    }
  }
  return null;
}

/**
 * @param {!Array<!Object>} contacts
 * @param {!Date} today
 * @return {!Array<!Object>}
 */
function findMatches_(contacts, today) {
  const matches = [];

  contacts.forEach((contact) => {
    const occurrence = nextOccurrence_(contact.month, contact.day, today);
    const days = daysBetween_(today, occurrence);
    if (REMIND_DAYS.indexOf(days) === -1) {
      return;
    }
    matches.push({
      name: contact.name,
      days: days,
      occurrence: occurrence,
      age: contact.year ? occurrence.getFullYear() - contact.year : null,
    });
  });

  matches.sort((left, right) => left.days - right.days || left.name.localeCompare(right.name));
  return matches;
}

/**
 * Next time this month and day come around, today included.
 * A Feb 29 birthday rolls to Mar 1 in non-leap years.
 *
 * @param {number} month
 * @param {number} day
 * @param {!Date} today
 * @return {!Date}
 */
function nextOccurrence_(month, day, today) {
  const occurrence = new Date(today.getFullYear(), month - 1, day);
  if (occurrence.getTime() >= today.getTime()) {
    return occurrence;
  }
  return new Date(today.getFullYear() + 1, month - 1, day);
}

/**
 * @param {!Date} from
 * @param {!Date} to
 * @return {number}
 */
function daysBetween_(from, to) {
  return Math.round((to.getTime() - from.getTime()) / MILLIS_PER_DAY);
}

/**
 * Midnight today in the given time zone.
 *
 * @param {string} timeZone
 * @return {!Date}
 */
function startOfToday_(timeZone) {
  const parts = Utilities.formatDate(new Date(), timeZone, 'yyyy-MM-dd').split('-');
  return new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
}

/**
 * @param {!Array<!Object>} matches
 * @return {string}
 */
function buildMessage_(matches) {
  const timeZone = Session.getScriptTimeZone();
  const lines = ['<b>Birthdays</b>', ''];

  matches.forEach((match) => {
    const date = Utilities.formatDate(match.occurrence, timeZone, 'EEE, MMM d');
    let line = `• ${escapeHtml_(match.name)} — ${relativeDay_(match.days)} (${date})`;
    if (match.age !== null) {
      line += `, turning ${match.age}`;
    }
    lines.push(line);
  });

  return lines.join('\n');
}

/**
 * @param {number} days
 * @return {string}
 */
function relativeDay_(days) {
  if (days === 0) {
    return 'today';
  }
  if (days === 1) {
    return 'tomorrow';
  }
  return `in ${days} days`;
}

/**
 * @param {string} text
 * @return {string}
 */
function escapeHtml_(text) {
  return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/**
 * Sends a message to the private chat, splitting it if Telegram would reject it.
 *
 * @param {string} text
 */
function sendTelegram_(text) {
  const properties = PropertiesService.getScriptProperties();
  const token = properties.getProperty(TOKEN_PROPERTY);
  const chatId = properties.getProperty(CHAT_ID_PROPERTY);
  if (!token || !chatId) {
    throw new Error(`${TOKEN_PROPERTY} and ${CHAT_ID_PROPERTY} must be set in Script Properties`);
  }

  const baseUrl = (properties.getProperty(BASE_URL_PROPERTY) || DEFAULT_API_BASE_URL).replace(/\/+$/, '');

  chunk_(text).forEach((part) => {
    const response = UrlFetchApp.fetch(`${baseUrl}/bot${token}/sendMessage`, {
      method: 'post',
      payload: {
        chat_id: chatId,
        text: part,
        parse_mode: 'HTML',
      },
      muteHttpExceptions: true,
    });

    const body = response.getContentText();
    const code = response.getResponseCode();
    if (code !== 200) {
      throw new Error(`Telegram API returned HTTP ${code}: ${body}`);
    }
    if (!JSON.parse(body).ok) {
      throw new Error(`Telegram API error: ${body}`);
    }
  });
}

/**
 * Splits text on line boundaries so every part stays under the Telegram limit.
 *
 * @param {string} text
 * @return {!Array<string>}
 */
function chunk_(text) {
  if (text.length <= MESSAGE_LIMIT) {
    return [text];
  }

  const parts = [];
  let current = '';

  text.split('\n').forEach((line) => {
    const candidate = current ? `${current}\n${line}` : line;
    if (candidate.length > MESSAGE_LIMIT && current) {
      parts.push(current);
      current = line;
    } else {
      current = candidate;
    }
  });

  if (current) {
    parts.push(current);
  }
  return parts;
}

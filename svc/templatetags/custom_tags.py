from django import template

register = template.Library()


@register.filter
def unique_vehicles(services):
    vehicles = set(service.vehicle for service in services)
    return list(vehicles)


@register.filter
def sub(value, arg):
    return value - arg


def number_to_words(number):
    def get_word(n):
        units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
                 "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

        if n < 20:
            return units[n]

        if n < 100:
            return tens[n // 10] + (" " + units[n % 10] if n % 10 != 0 else "")

        if n < 1000:
            return units[n // 100] + " Hundred" + (" and " + get_word(n % 100) if n % 100 != 0 else "")

        if n < 100000:
            return get_word(n // 1000) + " Thousand" + (" " + get_word(n % 1000) if n % 1000 != 0 else "")

        if n < 10000000:
            return get_word(n // 100000) + " Lakh" + (" " + get_word(n % 100000) if n % 100000 != 0 else "")

        return get_word(n // 10000000) + " Crore" + (" " + get_word(n % 10000000) if n % 10000000 != 0 else "")

    try:
        number = float(number)
        rupees = int(number)
        paise = int((number - rupees) * 100)

        rupees_in_words = get_word(rupees) + " Rupees"
        if paise > 0:
            return rupees_in_words + " and " + get_word(paise) + " Paise"
        return rupees_in_words
    except:
        return ""


register.filter('number_to_words', number_to_words)
